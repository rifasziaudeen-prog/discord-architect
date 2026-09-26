"""
config.py
=========
Global configuration, environment variable loaders, and dynamic guild settings management
for Discord Server Architect Bot. Zero hardcoded Discord IDs.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

import discord
from discord.ext import commands

# Load .env file
load_dotenv()

logger = logging.getLogger("architect.config")

# ── Core Environment Variables ────────────────────────────────────────
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "").strip()

# Gemini API Keys: supports comma-separated list for failover
_raw_gemini = os.getenv("GEMINI_API_KEYS", "") or os.getenv("GEMINI_API_KEY", "")
GEMINI_API_KEYS: List[str] = [k.strip() for k in _raw_gemini.split(",") if k.strip()]

# Bot Owner ID (Optional: if empty, bot application owner is used dynamically)
_raw_owner = os.getenv("BOT_OWNER_ID", "").strip()
BOT_OWNER_ID: Optional[int] = int(_raw_owner) if _raw_owner.isdigit() else None

COMMAND_PREFIX: str = os.getenv("COMMAND_PREFIX", "!").strip()
DEFAULT_AI_MODEL: str = os.getenv("DEFAULT_AI_MODEL", "gemini-3.1-flash-lite").strip()
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").strip().upper()

# UI Theme Palette (Cyberpunk / Glassmorphic)
COLOR_CYAN = "#00E5FF"
COLOR_PURPLE = "#9D00FF"
COLOR_DANGER = "#FF0055"
COLOR_SUCCESS = "#00FF88"

# Cached GenAI clients
_GEMINI_CLIENTS: Dict[str, Any] = {}


def get_gemini_client(api_key: str) -> Optional[Any]:
    """Returns a cached genai.Client instance for the provided API key."""
    if not api_key:
        return None
    if api_key not in _GEMINI_CLIENTS:
        try:
            from google import genai
            _GEMINI_CLIENTS[api_key] = genai.Client(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to create Google GenAI client: {e}")
            return None
    return _GEMINI_CLIENTS.get(api_key)


# ── Dynamic Guild Settings Store ──────────────────────────────────────
class GuildConfigManager:
    """Lightweight, zero-external-database JSON persistence for guild settings.
    Stores authorized architect roles, log channels, and AI toggles dynamically.
    """

    def __init__(self, data_path: Optional[str] = None):
        if data_path:
            self.file_path = Path(data_path)
        else:
            self.file_path = Path(__file__).parent / "data" / "guild_configs.json"

        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._configs: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self) -> None:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    self._configs = json.load(f)
            except Exception as err:
                logger.error(f"Failed to load guild configs from {self.file_path}: {err}")
                self._configs = {}
        else:
            self._configs = {}

    def _save(self) -> None:
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self._configs, f, indent=2)
        except Exception as err:
            logger.error(f"Failed saving guild configs: {err}")

    def get_guild_config(self, guild_id: int) -> Dict[str, Any]:
        """Returns the configuration dict for a guild."""
        gid = str(guild_id)
        if gid not in self._configs:
            self._configs[gid] = {
                "architect_role_id": None,
                "log_channel_id": None,
                "ai_chat_enabled": True,
            }
        return self._configs[gid]

    def set_architect_role(self, guild_id: int, role_id: Optional[int]) -> None:
        """Sets or clears the designated architect role for a guild."""
        cfg = self.get_guild_config(guild_id)
        cfg["architect_role_id"] = role_id
        self._save()

    def set_log_channel(self, guild_id: int, channel_id: Optional[int]) -> None:
        """Sets or clears the designated audit log channel for a guild."""
        cfg = self.get_guild_config(guild_id)
        cfg["log_channel_id"] = channel_id
        self._save()

    def set_ai_chat_enabled(self, guild_id: int, enabled: bool) -> None:
        """Toggles conversational AI responses in this guild."""
        cfg = self.get_guild_config(guild_id)
        cfg["ai_chat_enabled"] = bool(enabled)
        self._save()

    def is_authorized(self, member: discord.Member, bot: commands.Bot) -> bool:
        """Verifies if a member has clearance to execute architect operations.
        Zero hardcoded IDs. Evaluates:
        1. Configured BOT_OWNER_ID (env)
        2. Dynamic Bot Application Owner (from Discord API)
        3. Guild Server Owner
        4. Guild Administrator permission
        5. Configured guild-specific Architect Role
        """
        # 1. Env configured bot owner
        if BOT_OWNER_ID and member.id == BOT_OWNER_ID:
            return True

        # 2. Dynamic Bot Application Owner (Supports both User and Team applications)
        if bot and getattr(bot, "application", None):
            owner = bot.application.owner
            if owner:
                if getattr(owner, "members", None):  # Team account
                    if any(m.id == member.id for m in owner.members):
                        return True
                elif member.id == owner.id:  # User account
                    return True

        # 3. Guild Server Owner
        if member.guild and member.id == member.guild.owner_id:
            return True

        # 4. Discord Administrator permission
        if getattr(member, "guild_permissions", None) and member.guild_permissions.administrator:
            return True

        # 5. Guild-configured Architect Role
        if member.guild:
            cfg = self.get_guild_config(member.guild.id)
            arch_role_id = cfg.get("architect_role_id")
            if arch_role_id and any(r.id == arch_role_id for r in member.roles):
                return True

        return False


# Singleton configuration manager instance
guild_config_manager = GuildConfigManager()
