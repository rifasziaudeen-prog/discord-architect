"""
cogs/ai_chat.py
===============
Conversational AI Cog for Ciel Architect Bot.
Houses Ciel's charming, witty anime persona, in-memory conversation memory,
and zero-token architect intent routing.
"""

import re
import logging
from collections import defaultdict
from typing import Dict, List, Optional

import discord
from discord.ext import commands

from config import (
    GEMINI_API_KEYS,
    DEFAULT_AI_MODEL,
    get_gemini_client,
    guild_config_manager,
    COLOR_CYAN,
)
from architect.agent import ArchitectAgent
from architect.service import GuildArchitectService

logger = logging.getLogger("ciel.ai_chat")

try:
    from google.genai import types
except ImportError:
    types = None


CIEL_PERSONA_PROMPT = """You are Ciel, an expressive, witty, and charming anime companion AI.
Personality & Style:
- Highly intelligent, perceptive, and naturally conversational.
- Confident, playful, and sharp. Never sound like a generic, robotic customer support assistant.
- In Discord servers, communicate concisely and engagingly (1-3 sentences for casual banter; thorough and organized for technical questions).
- Prohibition: Do NOT use generic unicode emojis. Use minimalist text indicators ('✦', '•') or clean markdown formatting instead.
"""


class AIChat(commands.Cog, name="AIChat"):
    """Handles natural conversational interactions and intent routing."""

    # Zero-token intent regex: detects requests meant for the architect sub-engine
    _ARCHITECT_INTENT_RE = re.compile(
        r"\b("
        r"(setup|scaffold|build|reorganize|redesign)\s+(a\s+|an\s+|the\s+|new\s+|this\s+|all\s+|every\s+)*(server|channels?|roles?|categories|category|verification|rules|automod|layout|onboarding)|"
        r"(create|make|add)\s+(a\s+|an\s+|the\s+|new\s+|this\s+|all\s+|every\s+)*(category|categories|channels?|roles?|verification|rules|automod|onboarding)|"
        r"deploy\s+(a\s+|an\s+|the\s+|new\s+|this\s+|all\s+|every\s+)*(verification|rules|server\s+guide|automod|blueprint|onboarding)|"
        r"(wipe|purge|delete|remove)\s+(a\s+|an\s+|the\s+|new\s+|this\s+|all\s+|every\s+)*(channels?|category|categories|roles?)|"
        r"onboarding\s+(audit|status|check|suggest|suggestions?|setup|config|configure|questions?)|"
        r"(audit|check|suggest|configure)\s+(our\s+)?(community\s+)?onboarding|"
        r"community\s+onboarding|"
        r"assign\s+(a\s+|the\s+)?role|"
        r"remove\s+(a\s+|the\s+)?role|"
        r"guild\s+genesis"
        r")\b",
        re.IGNORECASE
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.architect_service = GuildArchitectService(bot)
        self.architect_agent = ArchitectAgent(bot, self.architect_service)
        # In-memory rolling conversation history per channel: channel_id -> list of {"role": str, "content": str}
        self.channel_history: Dict[int, List[Dict[str, str]]] = defaultdict(list)
        self.max_history_length = 10

    def _clean_content(self, message: discord.Message) -> str:
        """Strips bot mentions and leading command prefixes from message text."""
        raw = message.content
        if self.bot.user:
            raw = re.sub(rf'<@!?{self.bot.user.id}>', '', raw)
        return raw.strip()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Dispatches mentions and direct interactions."""
        if message.author.bot or not message.guild:
            return

        is_mentioned = self.bot.user and (self.bot.user in message.mentions or f"<@{self.bot.user.id}>" in message.content)
        cleaned_text = self._clean_content(message)

        if not is_mentioned or not cleaned_text:
            return

        # ── 1. ZERO-TOKEN ARCHITECT INTENT GATE ─────────────────────────
        # If user is asking for channel/role/server setup, execute via ArchitectAgent
        # This incurs 0 chat prompt tokens and gives instant precision.
        if self._ARCHITECT_INTENT_RE.search(cleaned_text):
            handled = await self.architect_agent.handle_architect_prompt(message, cleaned_text)
            if handled:
                return

        # ── 2. CASUAL CONVERSATIONAL CHAT ─────────────────────────────
        guild_cfg = guild_config_manager.get_guild_config(message.guild.id)
        if not guild_cfg.get("ai_chat_enabled", True):
            return

        if not GEMINI_API_KEYS:
            await message.channel.send("`[SYSTEM FAULT]` No Gemini API keys configured.")
            return

        async with message.channel.typing():
            # Build conversation context
            history = self.channel_history[message.channel.id]
            history.append({"role": "user", "name": message.author.display_name, "content": cleaned_text})

            # Trim history to max length
            if len(history) > self.max_history_length:
                self.channel_history[message.channel.id] = history[-self.max_history_length:]
                history = self.channel_history[message.channel.id]

            # Construct history prompt
            convo_blocks = []
            for item in history:
                name = item.get("name", "User")
                convo_blocks.append(f"{name}: {item['content']}")

            prompt_body = (
                f"Current Speaker: {message.author.display_name} (<@{message.author.id}>)\n"
                f"Server: {message.guild.name}\n\n"
                f"Recent Conversation:\n"
                + "\n".join(convo_blocks)
            )

            models_to_try = [DEFAULT_AI_MODEL, "gemini-2.5-flash", "gemini-3.5-flash-lite"]
            reply_text = None

            for model_name in models_to_try:
                for idx, key in enumerate(GEMINI_API_KEYS):
                    client = get_gemini_client(key)
                    if not client:
                        continue
                    try:
                        resp = await client.aio.models.generate_content(
                            model=model_name,
                            contents=prompt_body,
                            config=types.GenerateContentConfig(
                                system_instruction=CIEL_PERSONA_PROMPT,
                                temperature=0.7
                            )
                        )
                        if resp and resp.text:
                            reply_text = resp.text.strip()
                            break
                    except Exception as err:
                        logger.warning(f"[AI CHAT] Model '{model_name}' key #{idx+1} error: {err}")
                if reply_text:
                    break

            if reply_text:
                history.append({"role": "model", "name": "Ciel", "content": reply_text})
                # Check message length for Discord limit
                if len(reply_text) > 2000:
                    for chunk in [reply_text[i:i+1990] for i in range(0, len(reply_text), 1990)]:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(reply_text)
            else:
                await message.channel.send("`[COMMUNICATION FAULT]` Ciel cognitive core timed out.")


async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))
