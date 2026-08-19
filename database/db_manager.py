"""
Async SQLite Database Manager for Gandiva Tunes.
Handles Guild Settings (setup channel, 24/7 mode, No-Prefix options) & User Playlists.
Credits: Syko Reddy
"""

import aiosqlite
from typing import Optional, List, Dict, Tuple, Any
from config import DATABASE_PATH


class DatabaseManager:
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Initialize all database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            # Guild settings table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    music_channel_id INTEGER,
                    music_message_id INTEGER,
                    is_247 INTEGER DEFAULT 0,
                    prefix TEXT DEFAULT '!',
                    volume INTEGER DEFAULT 80,
                    noprefix_enabled INTEGER DEFAULT 1
                )
            """)

            # Server-wide No-Prefix user list
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_noprefix (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    PRIMARY KEY (guild_id, user_id)
                )
            """)

            # User playlists table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_playlists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, name)
                )
            """)

            # Playlist tracks table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS playlist_tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    playlist_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    duration INTEGER DEFAULT 0,
                    thumbnail TEXT,
                    position INTEGER DEFAULT 0,
                    FOREIGN KEY (playlist_id) REFERENCES user_playlists (id) ON DELETE CASCADE
                )
            """)
            await db.commit()

    # ----------------- GUILD SETTINGS -----------------

    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Fetch settings for a guild."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return {
                    "guild_id": guild_id,
                    "music_channel_id": None,
                    "music_message_id": None,
                    "is_247": 0,
                    "prefix": "!",
                    "volume": 80,
                    "noprefix_enabled": 1,
                }

    async def set_music_channel(self, guild_id: int, channel_id: int, message_id: int):
        """Save dedicated music setup channel & persistent message ID."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, music_channel_id, music_message_id)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    music_channel_id = excluded.music_channel_id,
                    music_message_id = excluded.music_message_id
            """, (guild_id, channel_id, message_id))
            await db.commit()

    async def get_music_channel(self, guild_id: int) -> Tuple[Optional[int], Optional[int]]:
        """Get (channel_id, message_id) for the music channel."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT music_channel_id, music_message_id FROM guild_settings WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return row[0], row[1]
                return None, None

    async def set_247(self, guild_id: int, status: bool):
        """Set 24/7 voice status for a guild."""
        val = 1 if status else 0
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, is_247)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    is_247 = excluded.is_247
            """, (guild_id, val))
            await db.commit()

    async def get_247(self, guild_id: int) -> bool:
        """Check if 24/7 mode is enabled for a guild."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT is_247 FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and row[0] == 1:
                    return True
                return False

    async def set_prefix(self, guild_id: int, prefix: str):
        """Set custom prefix for a guild."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, prefix)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    prefix = excluded.prefix
            """, (guild_id, prefix))
            await db.commit()

    async def get_prefix(self, guild_id: int) -> str:
        """Get prefix for a guild."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT prefix FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row and row[0]:
                    return row[0]
                return "!"

    # ----------------- NO-PREFIX SETTINGS -----------------

    async def set_server_noprefix(self, guild_id: int, enabled: bool):
        """Enable or disable server-wide No-Prefix mode."""
        val = 1 if enabled else 0
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO guild_settings (guild_id, noprefix_enabled)
                VALUES (?, ?)
                ON CONFLICT(guild_id) DO UPDATE SET
                    noprefix_enabled = excluded.noprefix_enabled
            """, (guild_id, val))
            await db.commit()

    async def is_server_noprefix_enabled(self, guild_id: int) -> bool:
        """Check if No-Prefix mode is enabled server-wide."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT noprefix_enabled FROM guild_settings WHERE guild_id = ?", (guild_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row is not None and row[0] is not None:
                    return row[0] == 1
                return True # Enabled by default for setup channel

    async def add_user_noprefix(self, guild_id: int, user_id: int) -> bool:
        """Grant a specific user No-Prefix permission in this guild."""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO user_noprefix (guild_id, user_id) VALUES (?, ?)",
                    (guild_id, user_id),
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def remove_user_noprefix(self, guild_id: int, user_id: int) -> bool:
        """Revoke a user's No-Prefix permission in this guild."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM user_noprefix WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def is_user_noprefix_allowed(self, guild_id: int, user_id: int) -> bool:
        """Check if user has No-Prefix permission."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT 1 FROM user_noprefix WHERE guild_id = ? AND user_id = ?",
                (guild_id, user_id),
            ) as cursor:
                row = await cursor.fetchone()
                return row is not None

    async def get_user_noprefix_list(self, guild_id: int) -> List[int]:
        """Get all user IDs with No-Prefix permission in this guild."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_id FROM user_noprefix WHERE guild_id = ?",
                (guild_id,),
            ) as cursor:
                rows = await cursor.fetchall()
                return [r[0] for r in rows]

    # ----------------- USER PLAYLISTS -----------------

    async def create_playlist(self, user_id: int, name: str) -> bool:
        """Create a new playlist for user. Returns True on success, False if already exists."""
        clean_name = name.strip()
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(
                    "INSERT INTO user_playlists (user_id, name) VALUES (?, ?)",
                    (user_id, clean_name),
                )
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False

    async def get_user_playlists(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all playlists owned by a user with track counts."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT p.id, p.name, p.created_at, COUNT(t.id) as track_count
                FROM user_playlists p
                LEFT JOIN playlist_tracks t ON p.id = t.playlist_id
                WHERE p.user_id = ?
                GROUP BY p.id
                ORDER BY p.name ASC
            """
            async with db.execute(query, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_playlist_by_name(self, user_id: int, name: str) -> Optional[Dict[str, Any]]:
        """Get playlist record by name."""
        clean_name = name.strip()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT id, user_id, name, created_at FROM user_playlists WHERE user_id = ? AND LOWER(name) = LOWER(?)",
                (user_id, clean_name),
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def add_track_to_playlist(
        self,
        user_id: int,
        playlist_name: str,
        title: str,
        url: str,
        duration: int = 0,
        thumbnail: str = "",
    ) -> bool:
        """Add a track to a user playlist."""
        playlist = await self.get_playlist_by_name(user_id, playlist_name)
        if not playlist:
            return False

        playlist_id = playlist["id"]
        async with aiosqlite.connect(self.db_path) as db:
            # Find next position
            async with db.execute(
                "SELECT COALESCE(MAX(position), 0) + 1 FROM playlist_tracks WHERE playlist_id = ?",
                (playlist_id,),
            ) as cursor:
                pos_row = await cursor.fetchone()
                next_pos = pos_row[0] if pos_row else 1

            await db.execute("""
                INSERT INTO playlist_tracks (playlist_id, title, url, duration, thumbnail, position)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (playlist_id, title, url, duration, thumbnail, next_pos))
            await db.commit()
            return True

    async def get_playlist_tracks(self, user_id: int, playlist_name: str) -> List[Dict[str, Any]]:
        """Get all tracks in a playlist ordered by position."""
        playlist = await self.get_playlist_by_name(user_id, playlist_name)
        if not playlist:
            return []

        playlist_id = playlist["id"]
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT id, title, url, duration, thumbnail, position
                FROM playlist_tracks
                WHERE playlist_id = ?
                ORDER BY position ASC, id ASC
            """
            async with db.execute(query, (playlist_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def remove_track_from_playlist(
        self, user_id: int, playlist_name: str, position_1_indexed: int
    ) -> bool:
        """Remove a track by its 1-indexed list position."""
        tracks = await self.get_playlist_tracks(user_id, playlist_name)
        if not (1 <= position_1_indexed <= len(tracks)):
            return False

        target_track = tracks[position_1_indexed - 1]
        track_id = target_track["id"]

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM playlist_tracks WHERE id = ?", (track_id,))
            await db.commit()
            return True

    async def delete_playlist(self, user_id: int, playlist_name: str) -> bool:
        """Delete an entire playlist."""
        playlist = await self.get_playlist_by_name(user_id, playlist_name)
        if not playlist:
            return False

        playlist_id = playlist["id"]
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM playlist_tracks WHERE playlist_id = ?", (playlist_id,))
            await db.execute("DELETE FROM user_playlists WHERE id = ?", (playlist_id,))
            await db.commit()
            return True


# Global database instance
db_manager = DatabaseManager()
