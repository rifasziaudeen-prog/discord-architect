"""
architect/agent.py
==================
Conversational Architect Coordinator for Ciel Architect Bot.
Invokes Google Gemini with compact tool declarations to design and configure Discord servers.
Enforces dynamic role authority, zero-emoji UI standards, and two-phase confirmation views.
"""

import logging
import discord
from discord.ext import commands
from typing import Optional, Dict, Any, List, Union

from config import (
    GEMINI_API_KEYS,
    DEFAULT_AI_MODEL,
    COLOR_CYAN,
    COLOR_PURPLE,
    COLOR_DANGER,
    COLOR_SUCCESS,
    get_gemini_client,
    guild_config_manager,
)
from .service import GuildArchitectService
from .schemas import get_architect_gemini_tools
from .views import ArchitectConfirmationView

logger = logging.getLogger("ciel.architect.agent")

try:
    from google.genai import types
except ImportError:
    types = None


ARCHITECT_SYSTEM_PROMPT = """You are Ciel's Autonomous Server Architect Sub-Engine.
Your mission is to analyze natural language requests from the server administrator and execute precise, high-craft Discord server management operations.

DIRECTIVES:
1. Always call the appropriate tool:
   - For multi-channel setups, layouts, full server designs, verification systems, or rules: call `apply_declarative_blueprint`.
   - For native Community Onboarding audits, status, or asking for recommendations: call `audit_community_onboarding`.
   - For deploying or updating native Community Onboarding questions and choices: call `configure_community_onboarding`.
   - For single channel creation, deletion, or renaming: call `manage_channel`.
   - For role creation, deletion, assignment, or permissions: call `manage_role`.
   - For channel wipes or resets: call `wipe_channels_preview`.
4. Format channel names in lowercase kebab-case (e.g. 'rules-and-info', 'general-chat', 'voice-lounge').
5. Build cohesive, elegant role hierarchies with hex colors (e.g. '#00E5FF', '#9D00FF', '#FF0055').
"""


class ArchitectAgent:
    """Coordinates Gemini function calling with GuildArchitectService."""

    def __init__(self, bot: commands.Bot, service: Optional[GuildArchitectService] = None):
        self.bot = bot
        self.service = service or GuildArchitectService(bot)

    def is_authorized(self, member: Union[discord.Member, discord.User]) -> bool:
        """Dynamic clearance check using GuildConfigManager. Zero hardcoded IDs."""
        if not isinstance(member, discord.Member):
            return False
        return guild_config_manager.is_authorized(member, self.bot)

    def build_server_snapshot(self, guild: discord.Guild) -> str:
        """Builds a token-efficient summary of the current guild structure."""
        categories = [c.name for c in guild.categories[:15]]
        text_channels = [c.name for c in guild.text_channels[:25]]
        roles = [r.name for r in guild.roles if r.name != "@everyone"][:20]

        return (
            f"[GUILD CONTEXT: {guild.name} (ID: {guild.id})]\n"
            f"- Member Count: {guild.member_count}\n"
            f"- Existing Categories ({len(categories)}): {', '.join(categories) if categories else 'None'}\n"
            f"- Existing Channels ({len(text_channels)}): {', '.join(text_channels) if text_channels else 'None'}\n"
            f"- Existing Roles ({len(roles)}): {', '.join(roles) if roles else 'None'}"
        )

    async def log_to_guild(self, guild: discord.Guild, embed: discord.Embed):
        """Sends an audit copy to the guild's configured log channel, if set."""
        cfg = guild_config_manager.get_guild_config(guild.id)
        log_ch_id = cfg.get("log_channel_id")
        if log_ch_id:
            ch = guild.get_channel(log_ch_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    await ch.send(embed=embed)
                except Exception as e:
                    logger.warning(f"Failed sending audit log to #{ch.name}: {e}")

    async def handle_architect_prompt(
        self,
        context_target: Union[discord.Message, discord.Interaction],
        clean_prompt: str
    ) -> bool:
        """Processes an architect request. Context target can be a Message or Interaction."""
        guild = context_target.guild
        author = context_target.author if isinstance(context_target, discord.Message) else context_target.user
        # Immediately defer interaction if needed to prevent 3-second Discord timeouts
        if isinstance(context_target, discord.Interaction):
            if not context_target.response.is_done():
                try:
                    await context_target.response.defer()
                except Exception:
                    pass

        async def reply(content=None, embed=None, view=None):
            if isinstance(context_target, discord.Interaction):
                return await context_target.followup.send(content=content, embed=embed, view=view)
            else:
                return await context_target.channel.send(content=content, embed=embed, view=view)

        if not guild:
            await reply("`[SECURITY]` Server architecture operations can only be executed within a Discord server.")
            return True

        if not self.is_authorized(author):
            embed = discord.Embed(
                title="[SECURITY INTERCEPT] Clearance Insufficient",
                description="Server architecture and layout commands are restricted to Server Administrators, the Server Owner, or the configured Architect Role.",
                color=discord.Color.from_str(COLOR_DANGER)
            )
            embed.set_footer(text="Ciel Security Matrix • Access Denied")
            await reply(embed=embed)
            return True

        if not GEMINI_API_KEYS:
            await reply("`[SYSTEM FAULT]` No Gemini API keys configured in .env (GEMINI_API_KEYS).")
            return True

        tools = get_architect_gemini_tools()
        if not tools:
            await reply("`[SYSTEM FAULT]` Google GenAI tool declarations could not be initialized.")
            return True

        # Provide typing indicator if message
        typing_ctx = context_target.channel.typing() if isinstance(context_target, discord.Message) else None
        if typing_ctx:
            await typing_ctx.__aenter__()

        try:
            guild_snapshot = self.build_server_snapshot(guild)
            user_content = f"{guild_snapshot}\n\n[ADMINISTRATOR INSTRUCTION]:\n{clean_prompt}"

            models_to_try = [DEFAULT_AI_MODEL, "gemini-3.1-flash-lite", "gemini-3.5-flash-lite", "gemini-flash-lite-latest", "gemini-3.8-flash"]
            # Deduplicate models list while preserving order
            seen_models = set()
            models_to_try = [m for m in models_to_try if not (m in seen_models or seen_models.add(m))]

            response = None
            for model_name in models_to_try:
                for idx, key in enumerate(GEMINI_API_KEYS):
                    client = get_gemini_client(key)
                    if not client:
                        continue
                    try:
                        response = await client.aio.models.generate_content(
                            model=model_name,
                            contents=user_content,
                            config=types.GenerateContentConfig(
                                system_instruction=ARCHITECT_SYSTEM_PROMPT,
                                temperature=0.15,
                                tools=tools
                            )
                        )
                        if response:
                            break
                    except Exception as err:
                        logger.warning(f"[ARCHITECT AGENT] Model '{model_name}' key #{idx+1} error: {err}")
                if response:
                    break

            if not response:
                await reply("`[ARCHITECT FAULT]` Failed to contact cognitive model. Verify API quotas.")
                return True

            # Process Function Calls
            tool_calls = getattr(response, "function_calls", None)
            if tool_calls:
                for call in tool_calls:
                    fn_name = call.name
                    fn_args = call.args or {}
                    logger.info(f"[ARCHITECT AGENT] Executing tool '{fn_name}' for guild '{guild.name}'")

                    # 1. Blueprint Deployment
                    if fn_name == "apply_declarative_blueprint":
                        result = await self.service.apply_declarative_blueprint(guild, fn_args)
                        embed = discord.Embed(
                            title=f"[ARCHITECT DEPLOYMENT] {guild.name}",
                            description="Declarative server blueprint compiled and applied.",
                            color=discord.Color.from_str(COLOR_CYAN)
                        )
                        if result.get("stages_executed"):
                            embed.add_field(
                                name="Stages Completed",
                                value="\n".join([f"• {s}" for s in result["stages_executed"]]),
                                inline=False
                            )
                        if result.get("errors"):
                            embed.add_field(
                                name="Errors / Warnings",
                                value="\n".join([f"• {e}" for e in result["errors"][:10]]),
                                inline=False
                            )
                        embed.set_footer(text="Project Ciel Autonomous Architect • Blueprint Pipeline")
                        await reply(embed=embed)
                        await self.log_to_guild(guild, embed)
                        return True

                    # 2. Channel CRUD
                    elif fn_name == "manage_channel":
                        result = await self.service.manage_channel(guild, **fn_args)
                        if result.get("success"):
                            embed = discord.Embed(
                                title=f"[CHANNEL MUTATION] {result.get('action', '').upper()}",
                                description=f"Successfully executed `{result.get('action')}` on #{result.get('channel_name')}.",
                                color=discord.Color.from_str(COLOR_CYAN)
                            )
                        else:
                            embed = discord.Embed(
                                title="[CHANNEL MUTATION FAULT]",
                                description=f"Execution failed: {result.get('error')}",
                                color=discord.Color.from_str(COLOR_DANGER)
                            )
                        embed.set_footer(text="Project Ciel Autonomous Architect")
                        await reply(embed=embed)
                        await self.log_to_guild(guild, embed)
                        return True

                    # 3. Role CRUD
                    elif fn_name == "manage_role":
                        result = await self.service.manage_role(guild, **fn_args)
                        if result.get("success"):
                            embed = discord.Embed(
                                title=f"[ROLE MUTATION] {result.get('action', '').upper()}",
                                description=f"Successfully executed `{result.get('action')}` on role **{result.get('role_name')}**.",
                                color=discord.Color.from_str(COLOR_PURPLE)
                            )
                        else:
                            embed = discord.Embed(
                                title="[ROLE MUTATION FAULT]",
                                description=f"Execution failed: {result.get('error')}",
                                color=discord.Color.from_str(COLOR_DANGER)
                            )
                        embed.set_footer(text="Project Ciel Autonomous Architect")
                        await reply(embed=embed)
                        await self.log_to_guild(guild, embed)
                        return True

                    # 4. Wipe Preview (Two-phase confirmation)
                    elif fn_name == "wipe_channels_preview":
                        keep = fn_args.get("keep_channels", [])
                        preview = await self.service.wipe_server_channels(guild, keep_channels=keep, simulate=True)
                        count = preview.get("channels_count", 0)

                        embed = discord.Embed(
                            title="[SECURITY WARNING: MASS CHANNEL PURGE]",
                            description=(
                                f"An administrator request was issued to purge **{count} channels**.\n"
                                f"Preserved channels: {', '.join(keep) if keep else 'None'}\n\n"
                                f"**This operation is irreversible.** Click below within 60 seconds to confirm."
                            ),
                            color=discord.Color.from_str(COLOR_DANGER)
                        )
                        view = ArchitectConfirmationView(author_id=author.id, timeout=60.0)
                        confirm_msg = await reply(embed=embed, view=view)

                        await view.wait()
                        if view.value is True:
                            wipe_res = await self.service.wipe_server_channels(guild, keep_channels=keep, simulate=False)
                            done_embed = discord.Embed(
                                title="[MASS PURGE COMPLETED]",
                                description=f"Permanently wiped {wipe_res.get('deleted_count', 0)} channels.",
                                color=discord.Color.from_str(COLOR_CYAN)
                            )
                            if isinstance(confirm_msg, discord.Message):
                                await confirm_msg.edit(embed=done_embed, view=None)
                            await self.log_to_guild(guild, done_embed)
                        return True

                    # 5. Native Community Onboarding Audit
                    elif fn_name == "audit_community_onboarding":
                        report = await self.service.audit_community_onboarding(guild)
                        has_comm = report.get("community_enabled", False)
                        is_active = report.get("onboarding_active", False)

                        embed = discord.Embed(
                            title=f"[COMMUNITY ONBOARDING AUDIT] {guild.name}",
                            description=(
                                f"**Community Feature**: `{'ACTIVE' if has_comm else 'DISABLED (Requires toggle in Server Settings)'}`\n"
                                f"**Onboarding Status**: `{'ACTIVE' if is_active else 'NOT CONFIGURED / DISABLED'}` (Mode: `{report.get('onboarding_mode', 'default')}`)"
                            ),
                            color=discord.Color.from_str(COLOR_CYAN if has_comm else COLOR_DANGER)
                        )

                        if report.get("blockers"):
                            embed.add_field(
                                name="Prerequisites & Blockers",
                                value="\n".join([f"• {b}" for b in report["blockers"]]),
                                inline=False
                            )

                        if report.get("current_prompts"):
                            p_lines = []
                            for p in report["current_prompts"]:
                                p_lines.append(f"• **{p['title']}** ({len(p.get('options', []))} options)")
                            embed.add_field(name="Current Prompts", value="\n".join(p_lines[:5]), inline=False)

                        if report.get("candidate_default_channels"):
                            embed.add_field(
                                name="Eligible Default Channels",
                                value=", ".join([f"#{c}" for c in report["candidate_default_channels"][:6]]),
                                inline=False
                            )

                        if report.get("suggestions"):
                            embed.add_field(
                                name="Ciel Architectural Recommendations",
                                value="\n".join([f"✦ {s}" for s in report["suggestions"]]),
                                inline=False
                            )

                        embed.set_footer(text="Project Ciel Autonomous Architect • Community Onboarding Engine")
                        await reply(embed=embed)
                        return True

                    # 6. Configure Native Community Onboarding
                    elif fn_name == "configure_community_onboarding":
                        res = await self.service.configure_community_onboarding(guild, **fn_args)
                        if res.get("success"):
                            embed = discord.Embed(
                                title=f"[COMMUNITY ONBOARDING DEPLOYED] {guild.name}",
                                description="Successfully updated native Discord Community Onboarding configuration.",
                                color=discord.Color.from_str(COLOR_PURPLE)
                            )
                            embed.add_field(name="Prompts Configured", value=f"`{res.get('prompts_count', 0)}` questions", inline=True)
                            embed.add_field(name="Default Channels", value=f"`{res.get('default_channels_count', 0)}` channels", inline=True)
                            if res.get("auto_created_roles"):
                                embed.add_field(
                                    name="Auto-Created Roles",
                                    value=", ".join([f"`@{r}`" for r in res["auto_created_roles"][:8]]),
                                    inline=False
                                )
                        else:
                            embed = discord.Embed(
                                title="[COMMUNITY ONBOARDING FAULT]",
                                description=f"Configuration failed: {res.get('error')}",
                                color=discord.Color.from_str(COLOR_DANGER)
                            )
                            if res.get("details"):
                                embed.add_field(name="Details", value="\n".join([f"• {d}" for d in res["details"][:5]]), inline=False)

                        embed.set_footer(text="Project Ciel Autonomous Architect • Native Discord API")
                        await reply(embed=embed)
                        await self.log_to_guild(guild, embed)
                        return True

            # If Gemini responded with plain conversational advice
            reply_text = (response.text or "").strip()
            if reply_text:
                embed = discord.Embed(
                    title="[ARCHITECT ADVISORY]",
                    description=reply_text,
                    color=discord.Color.from_str(COLOR_CYAN)
                )
                embed.set_footer(text="Project Ciel Autonomous Architect")
                await reply(embed=embed)
                return True

            return False
        finally:
            if typing_ctx:
                await typing_ctx.__aexit__(None, None, None)
