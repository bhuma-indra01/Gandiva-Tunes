"""
Neon & Glassmorphism UI Theme Builder for Gandiva Tunes Discord Bot.
Provides stylized embeds, glowing unicode boxes, progress bars, and branding.
Credits: Syko Reddy
"""

import discord
from typing import Optional, List, Dict, Any
from config import (
    BOT_NAME,
    BOT_TAGLINE,
    CREDITS_TEXT,
    CREDITS_FOOTER,
    COLOR_NEON_CYAN,
    COLOR_NEON_PINK,
    COLOR_NEON_PURPLE,
    COLOR_NEON_GREEN,
    COLOR_NEON_ORANGE,
    COLOR_GLASS_DARK,
    COLOR_ERROR,
    COLOR_SUCCESS,
)


def format_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds or seconds <= 0:
        return "00:00"
    seconds = int(seconds)
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def create_progress_bar(current: int, total: int, bar_length: int = 14) -> str:
    """Create a sleek neon-styled audio progress bar."""
    if total <= 0:
        return "🔴 LIVE STREAM"
    
    current = max(0, min(current, total))
    progress = current / total
    filled_length = int(bar_length * progress)
    
    # Sleek line characters
    filled_char = "━"
    empty_char = "─"
    indicator = "🔘"
    
    if filled_length == 0:
        bar = indicator + (empty_char * (bar_length - 1))
    elif filled_length >= bar_length:
        bar = (filled_char * (bar_length - 1)) + indicator
    else:
        bar = (filled_char * (filled_length - 1)) + indicator + (empty_char * (bar_length - filled_length))
    
    return f"`{format_duration(current)}` {bar} `{format_duration(total)}`"


def create_now_playing_embed(
    track: Dict[str, Any],
    current_pos: int = 0,
    is_paused: bool = False,
    volume: int = 80,
    loop_mode: str = "OFF", # "OFF", "TRACK", "QUEUE"
    filter_name: str = "Normal",
    is_247: bool = False,
    queue_len: int = 0,
) -> discord.Embed:
    """Create a Neon Glassmorphic Now Playing embed."""
    title = track.get("title", "Unknown Track")
    url = track.get("url", "https://discord.gg")
    duration = track.get("duration", 0)
    thumbnail = track.get("thumbnail") or track.get("artwork_url")
    author = track.get("author") or track.get("uploader") or "Unknown Artist"
    requester = track.get("requester")
    
    status_icon = "⏸️ PAUSED" if is_paused else "▶️ PLAYING"
    progress_bar = create_progress_bar(current_pos, duration)
    
    # Loop emoji
    loop_icons = {"OFF": "❌ Off", "TRACK": "🔂 Single", "QUEUE": "🔁 All"}
    loop_display = loop_icons.get(loop_mode, "❌ Off")
    mode_247_str = "🟢 Active" if is_247 else "⚪ Inactive"

    embed = discord.Embed(
        title=f"🏹 {BOT_NAME} ━ {status_icon}",
        description=(
            f"### 🎵 [{title}]({url})\n"
            f"**👤 Artist:** `{author}`\n"
            f"**⏱️ Progress:**\n{progress_bar}\n"
        ),
        color=COLOR_NEON_CYAN,
    )
    
    embed.add_field(name="🔊 Volume", value=f"`{volume}%`", inline=True)
    embed.add_field(name="🔁 Loop Mode", value=f"`{loop_display}`", inline=True)
    embed.add_field(name="⚡ Equalizer", value=f"`{filter_name}`", inline=True)
    embed.add_field(name="🕒 24/7 Mode", value=f"`{mode_247_str}`", inline=True)
    embed.add_field(name="📜 Queue Left", value=f"`{queue_len} song(s)`", inline=True)
    
    if requester:
        embed.add_field(name="🎧 Requested By", value=f"{requester.mention}", inline=True)

    if thumbnail:
        embed.set_thumbnail(url=thumbnail)

    embed.set_footer(
        text=f"{CREDITS_FOOTER} • Neon Glass UI",
        icon_url="https://cdn.discordapp.com/emojis/1044641887309991956.webp?size=96&quality=lossless"
    )
    return embed


def create_setup_idle_embed(prefix: str = "!") -> discord.Embed:
    """Create the persistent idle embed for #gandiva-tunes-music setup channel."""
    embed = discord.Embed(
        title=f"🏹 {BOT_NAME} ━ Dedicated Music Console",
        description=(
            f"```ansi\n"
            f"\u001b[1;36m╭──────────────────────────────────────────────╮\n"
            f"\u001b[1;35m│   🎵 GANDIVA TUNES - NO PREFIX MUSIC ZONE   │\n"
            f"\u001b[1;36m╰──────────────────────────────────────────────╯\u001b[0m\n"
            f"```\n"
            f"### 🚀 **How to Play Songs:**\n"
            f"Simply **type the song name or paste a YouTube / Spotify link** right here in this channel!\n"
            f"• No prefix or slash command needed in this channel.\n"
            f"• Your message will automatically disappear to keep chat crystal clean.\n"
            f"• Use the interactive neon buttons below to control audio in real time.\n\n"
            f"**Supported Links:** YouTube, Spotify, SoundCloud, MP3 Streams\n"
            f"**Owner/Credits:** `{CREDITS_TEXT}`\n"
        ),
        color=COLOR_NEON_PURPLE,
    )
    embed.set_image(url="https://i.imgur.com/8Q9Z8n9.png") # Clean aesthetic banner placeholder
    embed.set_footer(
        text=f"{CREDITS_FOOTER} • Ready to stream 24/7",
    )
    return embed


def create_queue_embed(
    queue_list: List[Dict[str, Any]],
    current_track: Optional[Dict[str, Any]],
    page: int = 1,
    per_page: int = 10,
) -> discord.Embed:
    """Create a sleek Neon Queue viewer embed."""
    total_tracks = len(queue_list)
    total_pages = max(1, (total_tracks + per_page - 1) // per_page)
    page = max(1, min(page, total_pages))
    
    embed = discord.Embed(
        title=f"🏹 {BOT_NAME} ━ Song Queue (Page {page}/{total_pages})",
        color=COLOR_NEON_PINK,
    )
    
    if current_track:
        c_title = current_track.get("title", "Unknown")
        c_url = current_track.get("url", "https://discord.gg")
        c_dur = format_duration(current_track.get("duration", 0))
        c_req = current_track.get("requester")
        req_str = f" • Requested by {c_req.mention}" if c_req else ""
        embed.description = f"**▶️ Now Playing:**\n[{c_title}]({c_url}) `[{c_dur}]`{req_str}\n\n**📜 Upcoming Tracks:**\n"
    else:
        embed.description = "**📜 Upcoming Tracks:**\n"

    if not queue_list:
        embed.description += "_No more tracks in queue. Add songs by typing their name!_"
    else:
        start_idx = (page - 1) * per_page
        end_idx = min(start_idx + per_page, total_tracks)
        
        for i in range(start_idx, end_idx):
            item = queue_list[i]
            t_title = item.get("title", "Unknown Track")
            t_url = item.get("url", "https://discord.gg")
            t_dur = format_duration(item.get("duration", 0))
            t_req = item.get("requester")
            r_mention = f" | {t_req.mention}" if t_req else ""
            embed.description += f"`{i+1}.` [{t_title}]({t_url}) `[{t_dur}]`{r_mention}\n"

    total_duration = sum(item.get("duration", 0) for item in queue_list)
    embed.set_footer(
        text=f"Total Songs: {total_tracks} • Total Queue Time: {format_duration(total_duration)} • {CREDITS_FOOTER}"
    )
    return embed


def create_success_embed(title: str, description: str) -> discord.Embed:
    """Create a sleek success notification embed."""
    embed = discord.Embed(
        title=f"✨ {title}",
        description=description,
        color=COLOR_SUCCESS,
    )
    embed.set_footer(text=CREDITS_FOOTER)
    return embed


def create_error_embed(title: str, description: str) -> discord.Embed:
    """Create a sleek error notification embed."""
    embed = discord.Embed(
        title=f"⚠️ {title}",
        description=description,
        color=COLOR_ERROR,
    )
    embed.set_footer(text=CREDITS_FOOTER)
    return embed


def create_credits_embed() -> discord.Embed:
    """Create the official credits and developer showcase embed."""
    embed = discord.Embed(
        title=f"🏹 {BOT_NAME} • Credits & Info",
        description=(
            f"```ansi\n"
            f"\u001b[1;36m╭──────────────────────────────────────────────╮\n"
            f"\u001b[1;32m│  🏹 GANDIVA TUNES - HIGH DEFINITION MUSIC    │\n"
            f"\u001b[1;36m╰──────────────────────────────────────────────╯\u001b[0m\n"
            f"```\n"
            f"### 👑 **Author & Developer:**\n"
            f"**Syko Reddy**\n\n"
            f"### 🌟 **Special Features:**\n"
            f"• 🎛️ **Dedicated Setup Channel** (`#gandiva-tunes-music`) with No-Prefix Auto-Play\n"
            f"• ⏱️ **Live Neon Progress Bar & Duration Timing**\n"
            f"• 🔊 **Equalizer & Audio Filters** (Bassboost, 8D, Nightcore, Vaporwave)\n"
            f"• 📂 **Personal Cloud Playlists** (Save your favorite songs to database)\n"
            f"• 🕒 **24/7 Non-Stop Voice Stay** (`/247`)\n"
            f"• 🖼️ **Bot Owner Avatar & Banner Changer (with animated GIF support)**\n"
            f"• 🚀 **Railway.app 1-Click Deployment Ready**\n"
        ),
        color=COLOR_NEON_CYAN,
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1044641887309991956.webp?size=96&quality=lossless")
    embed.set_footer(text=CREDITS_FOOTER)
    return embed
