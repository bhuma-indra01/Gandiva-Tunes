# 🏹 Gandiva Tunes — All-In-One Discord Music Bot

> **Created & Developed by:** **Syko Reddy**  
> **Aesthetic Theme:** Neon Glassmorphism  
> **Supported Platforms:** **Railway.app** & **Render.com** (Dual Deploy Ready!)

---

## ✨ Key Features

1. 🎛️ **Dedicated Setup Channel (`#gandiva-tunes-music`)**:
   - Run `/setup` to automatically create a dedicated music channel.
   - **No-Prefix Auto-Play:** Users simply type a song title or paste a YouTube / Spotify link.
   - **Auto-Delete Cleaner:** The bot immediately deletes the user's message to keep the channel pristine.
   - **Persistent Interactive Controller Panel:** Control playback in real-time with glowing Neon UI buttons.

2. ⏱️ **Live Music Progress Bar & Timestamps**:
   - Displays real-time audio progress: `01:23 ━━━🔘──────── 03:45`.
   - Updated dynamically on both the dedicated panel and now-playing embeds.

3. 📂 **Personal Cloud Playlist System (SQLite)**:
   - Users can save and organize their favorite songs into private cloud playlists.
   - Commands: `/playlist create`, `/playlist add`, `/playlist play`, `/playlist list`, `/playlist view`, `/playlist remove`, `/playlist delete`.

4. 🕒 **24/7 Voice Stay Mode (`/247`)**:
   - Keep Gandiva Tunes permanently connected in your server's voice channel even when idle.

5. ⚡ **Audio Equalizers & DSP Filters**:
   - Real-time hardware FFmpeg filters: **Bassboost**, **Extreme Bass**, **8D Spatial Audio**, **Nightcore**, **Vaporwave**, **Pop**, **Treble**, **Karaoke**, and **Reset**.

6. 🖼️ **Bot Owner Profile & Banner Updater (GIF Support)**:
   - Exclusive to the Bot Owner (`Syko Reddy`):
   - `/setavatar` — Change bot profile picture (supports static images & **animated GIFs**!).
   - `/setbanner` — Change bot profile banner (supports static images & **animated GIFs**!).
   - `/setname` — Update bot username.
   - `/setstatus` — Set custom presence (Listening, Playing, Streaming, Watching).

7. 🚀 **Dual Cloud Deployment (Railway & Render Ready)**:
   - Pre-configured with `railway.json`, `nixpacks.toml`, `Dockerfile`, `render.yaml`, `Procfile`, and `keep_alive.py`.

---

## 🛠️ Step 1: Discord Developer Portal Setup

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application**, enter the name **Gandiva Tunes**, and click **Create**.
3. Go to the **Bot** tab on the left menu:
   - Click **Reset Token** and copy your **Bot Token** (keep this secret!).
   - Scroll down to **Privileged Gateway Intents** and **ENABLE ALL THREE**:
     - ✅ **PRESENCE INTENT**
     - ✅ **SERVER MEMBERS INTENT**
     - ✅ **MESSAGE CONTENT INTENT** (Crucial for no-prefix music requests!)
4. Go to the **OAuth2 -> URL Generator** tab:
   - Under **Scopes**, select: `bot` and `applications.commands`.
   - Under **Bot Permissions**, select: `Administrator` (or *Send Messages, Manage Messages, Embed Links, Attach Files, Read Message History, Connect, Speak, Manage Channels*).
   - Copy the generated URL and paste it into your browser to invite Gandiva Tunes to your Discord server!
5. **Get Your Discord User ID (Bot Owner ID)**:
   - In Discord, go to **User Settings -> Advanced -> Enable Developer Mode**.
   - Right-click your profile picture and click **Copy User ID**.

---

## 🚀 Step 2: Deployment (Choose Railway OR Render)

### 🚂 Option A: Deploy to Railway.app (Primary)

1. Extract `Gandiva_Tunes_Bot.zip` and upload/push the files to a **GitHub repository**.
2. Log in to [Railway.app](https://railway.app/).
3. Click **+ New Project** -> **Deploy from GitHub repo**.
4. Select your Gandiva Tunes repository.
5. Go to the **Variables** tab in your Railway service and add:
   - `DISCORD_TOKEN` = `your_discord_bot_token_here`
   - `OWNER_ID` = `your_discord_user_id_here`
   - `DEFAULT_PREFIX` = `!` (Optional)
   - `SPOTIPY_CLIENT_ID` = *(Optional, for Spotify)*
   - `SPOTIPY_CLIENT_SECRET` = *(Optional, for Spotify)*
6. Railway will automatically build via `nixpacks.toml`, install FFmpeg, and run Gandiva Tunes!

---

### 🌐 Option B: Deploy to Render.com (Backup)

If Railway is down or you prefer Render:

1. Upload the project files to a **GitHub repository**.
2. Log in to [Render.com](https://dashboard.render.com/).
3. Click **New +** -> **Web Service**.
4. Connect your GitHub repository.
5. In the configuration settings:
   - **Environment:** `Docker` *(Recommended — uses our Dockerfile with FFmpeg pre-installed)*
   - **Plan:** `Free`
   - **Health Check Path:** `/health`
6. Under **Environment Variables**, add:
   - `DISCORD_TOKEN` = `your_discord_bot_token_here`
   - `OWNER_ID` = `your_discord_user_id_here`
   - `PORT` = `10000`
   - `DEFAULT_PREFIX` = `!`
7. Click **Create Web Service**.
8. Render will build the Docker container with FFmpeg and bind to the port using our built-in `keep_alive.py` web server!
   *(Tip: You can use [UptimeRobot](https://uptimerobot.com) to ping your Render URL every 5 minutes to keep it online 24/7).*

---

## 📋 Full Command Reference

### 🎛️ Setup & Configuration
| Command | Description |
|---|---|
| `/setup` | Creates `#gandiva-tunes-music` channel with interactive panel |
| `/247` | Toggles 24/7 voice channel stay mode |
| `/prefix <symbol>` | Changes the server command prefix |
| `/noprefix server <enable/disable>` | [Server Owner] Enables/disables No-Prefix server-wide |
| `/noprefix user <add/remove> <user>` | [Server Owner] Whitelists specific users for No-Prefix |
| `/noprefix list` | Views whitelisted No-Prefix users |

### 🎵 Music Playback
| Command | Aliases | Description |
|---|---|---|
| `/play <query/url>` | `!p` | Plays YouTube, Spotify, SoundCloud songs or playlists |
| `/pause` | | Pauses current playback |
| `/resume` | `!unpause` | Resumes playback |
| `/skip` | `!s`, `!next` | Skips to the next song |
| `/stop` | | Stops music and clears the queue |
| `/nowplaying` | `!np` | Shows current song info and live progress timing bar |
| `/queue [page]` | `!q` | Displays upcoming songs with interactive pagination |
| `/volume <0-150>` | `!vol` | Adjusts playback volume |
| `/loop <off/track/queue>` | | Toggles repeat mode |
| `/shuffle` | | Shuffles the song queue |
| `/remove <index>` | | Removes a specific track from the queue |
| `/clear` | | Clears all upcoming tracks |
| `/join` | | Joins your voice channel |
| `/leave` | `!dc` | Disconnects from voice channel |

### ⚡ Audio Filters & Equalizer
| Command | Description |
|---|---|
| `/filter Bassboost` | Boosts low-end bass frequencies |
| `/filter Extreme Bass` | Maximum bass distortion and rumble |
| `/filter 8D` | 360-degree spatial surround sound |
| `/filter Nightcore` | Sped-up tempo and higher pitch |
| `/filter Vaporwave` | Slowed retro aesthetic tempo |
| `/filter Pop` | Vocal and midrange enhancement |
| `/filter Treble` | High frequency boost |
| `/filter Karaoke` | Vocal suppression |
| `/filter Normal` | Resets all equalizer filters to default |
| `/equalizer_menu` | Opens interactive dropdown menu for filters |

### 📂 Personal Playlists
| Command | Description |
|---|---|
| `/playlist create <name>` | Creates a new personal cloud playlist |
| `/playlist add <name> <song/link>` | Adds a track to your personal playlist |
| `/playlist play <name>` | Loads and plays all songs from your playlist |
| `/playlist list` | Lists all your personal playlists |
| `/playlist view <name>` | Views tracks in a playlist |
| `/playlist remove <name> <#>` | Removes a track by position number |
| `/playlist delete <name>` | Permanently deletes a playlist |

### 👑 Bot Owner Commands (`Syko Reddy` only)
| Command | Description |
|---|---|
| `/setavatar <url/file>` | Updates bot avatar (supports static & **animated GIFs**) |
| `/setbanner <url/file>` | Updates bot profile banner (supports static & **animated GIFs**) |
| `/setname <name>` | Updates bot username |
| `/setstatus <type> <text>` | Updates bot presence activity |
| `/sync` | Forces global Slash Command synchronization |

### ℹ️ General & Info
| Command | Description |
|---|---|
| `/credits` | Displays official developer credits (`Syko Reddy`) |
| `/help` | Displays interactive help menu |
| `/ping` | Displays WebSocket and REST API latency |
| `/stats` | Displays bot uptime, server count, and memory stats |

---

## 👑 Credits & Author
- **Bot Name:** **Gandiva Tunes 🏹**
- **Created & Maintained by:** **Syko Reddy**
- **Support & License:** MIT License
