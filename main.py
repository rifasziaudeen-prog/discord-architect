"""
main.py
=======
Main entry point for Discord Server Architect Bot.
Initializes Discord client, synchronizes slash commands, and loads modular cogs.
"""

import os
import sys
import logging
import asyncio
from pathlib import Path

import discord
from discord.ext import commands

# Ensure package path is resolved
current_dir = Path(__file__).resolve().parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from config import (
    DISCORD_TOKEN,
    COMMAND_PREFIX,
    LOG_LEVEL,
    COLOR_CYAN,
)

# ── Structured Logging ────────────────────────────────────────────────
log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format=log_format,
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("architect.main")


class ServerArchitectBot(commands.Bot):
    """Autonomous server architect & setup Discord bot."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.messages = True
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=commands.when_mentioned_or(COMMAND_PREFIX),
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """Loads cogs and synchronizes global application slash commands."""
        try:
            self.application = await self.application_info()
            logger.info(f"[INIT] Bot application owner resolved: {self.application.owner}")
        except Exception as app_err:
            logger.warning(f"[INIT] Could not pre-fetch application info: {app_err}")

        logger.info("[INIT] Loading core cogs...")
        cogs_to_load = [
            "cogs.ai_chat",
            "cogs.architect_commands",
        ]

        for cog in cogs_to_load:
            try:
                await self.load_extension(cog)
                logger.info(f"[COG] Successfully loaded extension: {cog}")
            except Exception as e:
                logger.error(f"[COG FAULT] Failed loading {cog}: {e}", exc_info=True)

        logger.info("[INIT] Synchronizing global slash commands with Discord...")
        try:
            synced = await self.tree.sync()
            logger.info(f"[SLASH COMMANDS] Synchronized {len(synced)} application commands.")
        except Exception as err:
            logger.error(f"[SLASH COMMANDS FAULT] Synchronization failed: {err}")

    async def on_interaction(self, interaction: discord.Interaction):
        """Global handler for persistent button views across bot restarts."""
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            if custom_id.startswith("setup_verify:"):
                from architect.views import handle_verification_click
                await handle_verification_click(interaction)
                return

        await super().on_interaction(interaction)

    async def on_ready(self):
        """Invoked when bot establishes connection and state is ready."""
        bot_user = self.user
        owner_name = "Dynamic Resolution"
        if self.application and self.application.owner:
            owner_name = f"{self.application.owner.name} ({self.application.owner.id})"

        banner = f"""
================================================================
  DISCORD SERVER ARCHITECT · AUTONOMOUS SETUP BOT
================================================================
  Status      : ONLINE
  Bot Identity: {bot_user.name}#{bot_user.discriminator} (ID: {bot_user.id})
  Application : {self.application.name if self.application else 'Architect'}
  Owner       : {owner_name}
  Guilds      : {len(self.guilds)} connected
  Latency     : {round(self.latency * 1000, 2)} ms
  Design      : Glassmorphic Cyberpunk
================================================================
"""
        print(banner)
        logger.info(f"Connected to {len(self.guilds)} guilds. Latency: {round(self.latency * 1000, 2)}ms")

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="server architecture | /setup"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)


def main():
    if not DISCORD_TOKEN:
        logger.critical("[BOOT FAULT] DISCORD_TOKEN is missing. Provide it in .env or environment variables.")
        sys.exit(1)

    bot = ServerArchitectBot()

    try:
        bot.run(DISCORD_TOKEN, log_handler=None)
    except KeyboardInterrupt:
        logger.info("[SHUTDOWN] Interrupted by user. Exiting cleanly.")
    except Exception as exc:
        logger.critical(f"[RUNTIME CRASH] Fatal exception: {exc}", exc_info=True)


if __name__ == "__main__":
    main()
