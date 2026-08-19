"""
Configuration loader for Gandiva Tunes Discord Music Bot.
Created with credits to: Syko Reddy
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "database" / "gandiva_tunes.db"

# Ensure database directory exists
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

# Bot Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "").strip()
DEFAULT_PREFIX = os.getenv("DEFAULT_PREFIX", "!").strip()
OWNER_ID_STR = os.getenv("OWNER_ID", "0").strip()
OWNER_ID = int(OWNER_ID_STR) if OWNER_ID_STR.isdigit() else 0

# Spotify API Configuration
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID", "").strip()
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "").strip()

# Audio Playback Defaults
DEFAULT_VOLUME = int(os.getenv("DEFAULT_VOLUME", "80"))
IDLE_TIMEOUT = int(os.getenv("IDLE_TIMEOUT", "180")) # 3 minutes idle before leaving (unless 24/7 is on)

# Branding Details
BOT_NAME = "Gandiva Tunes"
BOT_TAGLINE = "🏹 Pure Sound, Epic Beats"
CREDITS_TEXT = "Syko Reddy"
CREDITS_FOOTER = "Gandiva Tunes 🏹 • Developed with ❤️ by Syko Reddy"

# Neon Glassmorphic Color Palette (Hex Integers)
COLOR_NEON_CYAN = 0x00F0FF
COLOR_NEON_PINK = 0xFF007F
COLOR_NEON_PURPLE = 0x9B51E0
COLOR_NEON_GREEN = 0x00FF88
COLOR_NEON_ORANGE = 0xFF7700
COLOR_GLASS_DARK = 0x1A1B26
COLOR_ERROR = 0xFF3366
COLOR_SUCCESS = 0x00FF99
