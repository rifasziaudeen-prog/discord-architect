"""
cogs/architect_commands.py
==========================
Application Slash Commands for Discord Server Architect.
Provides the streamlined /setup command suite, /status shortcut, and /ask assistant command
with dynamic role authority and zero hardcoded IDs.
"""

import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from config import (
    guild_config_manager,
    COLOR_CYAN,
    COLOR_PURPLE,
    COLOR_DANGER,
    COLOR_SUCCESS,
)
from architect.agent import ArchitectAgent
from architect.service import GuildArchitectService

logger = logging.getLogger("architect.commands")


class SetupCommands(commands.Cog, name="SetupCommands"):
    """Streamlined /setup command suite for Discord Server Architecture & Automation."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.service = GuildArchitectService(bot)
        self.agent = ArchitectAgent(bot, self.service)

    # ── THE CORE /setup COMMAND GROUP ─────────────────────────────────
    setup_group = app_commands.Group(
        name="setup",
        description="Autonomous Discord server setup, blueprints, onboarding, and configuration"
    )

    # 1. /setup config
    @setup_group.command(
        name="config",
        description="Configure architect authority roles, log channels, and AI settings for this server."
    )
    @app_commands.describe(
        role="Optional role granted server architect authority (in addition to Administrators)",
        log_channel="Channel where architect operations and blueprints are logged",
        ai_enabled="Enable or disable conversational AI chat in this server"
    )
    async def setup_config_cmd(
        self,
        interaction: discord.Interaction,
        role: Optional[discord.Role] = None,
        log_channel: Optional[discord.TextChannel] = None,
        ai_enabled: Optional[bool] = None
    ):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("`[ERROR]` Setup can only be executed inside a Discord server.", ephemeral=True)
            return

        if not guild_config_manager.is_authorized(interaction.user, self.bot):
            await interaction.response.send_message(
                "`[PERMISSION DENIED]` Only Server Administrators or the Guild Owner can configure Server Architect.",
                ephemeral=True
            )
            return

        await interaction.response.defer()
        cfg = guild_config_manager.get_guild_config(guild.id)
        updates = []

        if role is not None:
            guild_config_manager.set_architect_role(guild.id, role.id)
            updates.append(f"• Architect Authority Role: **@{role.name}**")

        if log_channel is not None:
            guild_config_manager.set_log_channel(guild.id, log_channel.id)
            updates.append(f"• Audit Log Channel: **#{log_channel.name}**")

        if ai_enabled is not None:
            guild_config_manager.set_ai_chat_enabled(guild.id, ai_enabled)
            updates.append(f"• Conversational AI: **{'ENABLED' if ai_enabled else 'DISABLED'}**")

        if not updates:
            await interaction.followup.send(
                "`[NOTICE]` No configuration parameters provided. Use `/setup status` to inspect current settings.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title=f"[ARCHITECT CONFIGURATION] {guild.name}",
            description="Server architecture settings updated successfully:\n\n" + "\n".join(updates),
            color=discord.Color.from_str(COLOR_SUCCESS)
        )
        embed.set_footer(text="Autonomous Server Architect • Dynamic Configuration")
        await interaction.followup.send(embed=embed)

    # 2. /setup status
    @setup_group.command(
        name="status",
        description="View current server architect configuration, permissions, and Community Onboarding readiness."
    )
    async def setup_status_cmd(self, interaction: discord.Interaction):
        await self._render_status(interaction)

    # 3. /setup blueprint
    @setup_group.command(
        name="blueprint",
        description="Deploy a declarative architecture layout via natural language prompt."
    )
    @app_commands.describe(prompt="Description of the server theme, categories, channels, or roles to build")
    async def setup_blueprint_cmd(self, interaction: discord.Interaction, prompt: str):
        if not guild_config_manager.is_authorized(interaction.user, self.bot):
            await interaction.response.send_message("`[PERMISSION DENIED]` Insufficient architect clearance.", ephemeral=True)
            return

        await interaction.response.defer()
        await self.agent.handle_architect_prompt(interaction, prompt)

    # 4. /setup onboarding
    @setup_group.command(
        name="onboarding",
        description="Inspect or configure Discord native Community Onboarding questions and choices."
    )
    @app_commands.describe(
        action="Audit current status or configure onboarding questions",
        prompt="Natural description of the questions and roles (for configure action)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Audit & Suggest", value="audit"),
        app_commands.Choice(name="Configure & Deploy", value="configure")
    ])
    async def setup_onboarding_cmd(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        prompt: Optional[str] = None
    ):
        if not guild_config_manager.is_authorized(interaction.user, self.bot):
            await interaction.response.send_message("`[PERMISSION DENIED]` Insufficient architect clearance.", ephemeral=True)
            return

        await interaction.response.defer()
        if action.value == "audit":
            query = "audit our community onboarding and report status and suggestions"
        else:
            query = f"configure community onboarding: {prompt or 'set up standard community onboarding'}"
        await self.agent.handle_architect_prompt(interaction, query)

    # 5. /setup channel
    @setup_group.command(
        name="channel",
        description="Create, delete, or edit a specific channel or category."
    )
    @app_commands.describe(
        action="Mutation operation to perform",
        name="Channel name or ID",
        category="Optional parent category name",
        channel_type="Channel type (text or voice)",
        topic="Channel description / topic"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Create", value="create"),
            app_commands.Choice(name="Delete", value="delete"),
            app_commands.Choice(name="Edit", value="edit"),
        ],
        channel_type=[
            app_commands.Choice(name="Text Channel", value="text"),
            app_commands.Choice(name="Voice Channel", value="voice"),
        ]
    )
    async def setup_channel_cmd(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        name: str,
        category: Optional[str] = None,
        channel_type: Optional[app_commands.Choice[str]] = None,
        topic: Optional[str] = None
    ):
        if not guild_config_manager.is_authorized(interaction.user, self.bot):
            await interaction.response.send_message("`[PERMISSION DENIED]` Insufficient architect clearance.", ephemeral=True)
            return

        await interaction.response.defer()
        ch_type = channel_type.value if channel_type else "text"
        res = await self.service.manage_channel(
            guild=interaction.guild,
            action=action.value,
            name=name,
            category=category,
            channel_type=ch_type,
            topic=topic
        )

        if res.get("success"):
            embed = discord.Embed(
                title=f"[CHANNEL MUTATION] {res.get('action', '').upper()}",
                description=f"Successfully executed `{res.get('action')}` on #{res.get('channel_name')}.",
                color=discord.Color.from_str(COLOR_CYAN)
            )
        else:
            embed = discord.Embed(
                title="[CHANNEL MUTATION FAULT]",
                description=f"Execution failed: {res.get('error')}",
                color=discord.Color.from_str(COLOR_DANGER)
            )
        embed.set_footer(text="Autonomous Server Architect")
        await interaction.followup.send(embed=embed)

    # 6. /setup role
    @setup_group.command(
        name="role",
        description="Create, delete, assign, or remove a server role."
    )
    @app_commands.describe(
        action="Mutation operation to perform",
        name="Role name or ID",
        color="Optional hex color (e.g. #00E5FF)",
        hoist="Display role separately in member list",
        target_user="Target member (for assign/remove)"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Create", value="create"),
            app_commands.Choice(name="Delete", value="delete"),
            app_commands.Choice(name="Assign", value="assign"),
            app_commands.Choice(name="Remove", value="remove"),
        ]
    )
    async def setup_role_cmd(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        name: str,
        color: Optional[str] = None,
        hoist: Optional[bool] = False,
        target_user: Optional[discord.Member] = None
    ):
        if not guild_config_manager.is_authorized(interaction.user, self.bot):
            await interaction.response.send_message("`[PERMISSION DENIED]` Insufficient architect clearance.", ephemeral=True)
            return

        await interaction.response.defer()
        u_str = str(target_user.id) if target_user else None
        res = await self.service.manage_role(
            guild=interaction.guild,
            action=action.value,
            name=name,
            color=color,
            hoist=bool(hoist),
            target_user=u_str
        )

        if res.get("success"):
            embed = discord.Embed(
                title=f"[ROLE MUTATION] {res.get('action', '').upper()}",
                description=f"Successfully executed `{res.get('action')}` on role **{res.get('role_name')}**.",
                color=discord.Color.from_str(COLOR_PURPLE)
            )
        else:
            embed = discord.Embed(
                title="[ROLE MUTATION FAULT]",
                description=f"Execution failed: {res.get('error')}",
                color=discord.Color.from_str(COLOR_DANGER)
            )
        embed.set_footer(text="Autonomous Server Architect")
        await interaction.followup.send(embed=embed)

    # 7. /setup wipe
    @setup_group.command(
        name="wipe",
        description="Safely reset channels with two-phase administrator confirmation."
    )
    @app_commands.describe(keep="Comma-separated channel names to preserve (e.g. general, rules)")
    async def setup_wipe_cmd(self, interaction: discord.Interaction, keep: Optional[str] = None):
        if not guild_config_manager.is_authorized(interaction.user, self.bot):
            await interaction.response.send_message("`[PERMISSION DENIED]` Insufficient architect clearance.", ephemeral=True)
            return

        await interaction.response.defer()
        keep_list = [k.strip() for k in keep.split(",")] if keep else []
        prompt = f"wipe all channels in this server{' keeping ' + ', '.join(keep_list) if keep_list else ''}"
        await self.agent.handle_architect_prompt(interaction, prompt)

    # ── STANDALONE SHORTCUT: /status ──────────────────────────────────
    @app_commands.command(
        name="status",
        description="Quick view of server architect configuration, telemetry, and permissions."
    )
    async def quick_status_cmd(self, interaction: discord.Interaction):
        await self._render_status(interaction)

    async def _render_status(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message("`[ERROR]` Must be executed inside a server.", ephemeral=True)
            return

        if not interaction.response.is_done():
            await interaction.response.defer()

        cfg = guild_config_manager.get_guild_config(guild.id)
        arch_role = guild.get_role(cfg.get("architect_role_id")) if cfg.get("architect_role_id") else None
        log_ch = guild.get_channel(cfg.get("log_channel_id")) if cfg.get("log_channel_id") else None
        ai_chat = cfg.get("ai_chat_enabled", True)

        has_community = "COMMUNITY" in guild.features
        bot_member = guild.me
        has_manage_guild = bot_member.guild_permissions.manage_guild
        has_manage_roles = bot_member.guild_permissions.manage_roles
        has_manage_channels = bot_member.guild_permissions.manage_channels

        embed = discord.Embed(
            title=f"[ARCHITECT MATRIX STATUS] {guild.name}",
            description="Server telemetry and autonomy configuration audit.",
            color=discord.Color.from_str(COLOR_CYAN)
        )

        embed.add_field(
            name="Configuration",
            value=(
                f"• Architect Role: {arch_role.mention if arch_role else '`None (Admins Only)`'}\n"
                f"• Log Channel: {log_ch.mention if log_ch else '`None`'}\n"
                f"• Conversational AI: `{'ENABLED' if ai_chat else 'DISABLED'}`"
            ),
            inline=False
        )

        embed.add_field(
            name="Community Features",
            value=(
                f"• Community Enabled: `{'ACTIVE' if has_community else 'DISABLED'}`\n"
                f"• Member Count: `{guild.member_count}`\n"
                f"• Channels: `{len(guild.channels)}` | Roles: `{len(guild.roles)}`"
            ),
            inline=False
        )

        embed.add_field(
            name="Bot Authority Diagnostics",
            value=(
                f"• Manage Channels: `{'GRANTED' if has_manage_channels else 'MISSING'}`\n"
                f"• Manage Roles: `{'GRANTED' if has_manage_roles else 'MISSING'}`\n"
                f"• Manage Server: `{'GRANTED' if has_manage_guild else 'MISSING'}`"
            ),
            inline=False
        )

        embed.set_footer(text="Autonomous Server Architect • System Diagnostics")
        await interaction.followup.send(embed=embed)

    # ── STANDALONE SHORTCUT: /ask ──────────────────────────────────────
    @app_commands.command(
        name="ask",
        description="Ask server engineering advice or issue natural language management commands."
    )
    @app_commands.describe(prompt="What would you like to ask or instruct the bot to do?")
    async def ask_command(self, interaction: discord.Interaction, prompt: str):
        if not interaction.response.is_done():
            await interaction.response.defer()

        handled = await self.agent.handle_architect_prompt(interaction, prompt)
        if not handled:
            from .ai_chat import ARCHITECT_ASSISTANT_PROMPT
            from config import GEMINI_API_KEYS, DEFAULT_AI_MODEL, get_gemini_client
            from google.genai import types

            if not GEMINI_API_KEYS:
                await interaction.followup.send("`[SYSTEM FAULT]` No Gemini API keys configured in .env.")
                return

            client = get_gemini_client(GEMINI_API_KEYS[0])
            if client:
                try:
                    resp = await client.aio.models.generate_content(
                        model=DEFAULT_AI_MODEL,
                        contents=f"User ({interaction.user.display_name}) says: {prompt}",
                        config=types.GenerateContentConfig(
                            system_instruction=ARCHITECT_ASSISTANT_PROMPT,
                            temperature=0.7
                        )
                    )
                    text = resp.text.strip() if resp and resp.text else "..."
                    await interaction.followup.send(text)
                    return
                except Exception as err:
                    logger.error(f"Failed generating AI reply: {err}")

            await interaction.followup.send("`[FAULT]` Failed generating response.")


async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCommands(bot))
