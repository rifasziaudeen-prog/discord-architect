"""
architect/views.py
==================
Zero-emoji interactive Discord UI Views for Ciel Architect Bot.
Adheres strictly to high-craft glassmorphic and semantic badge design standards.
"""

import logging
import discord
from typing import Optional

logger = logging.getLogger("ciel.architect.views")


class VerificationButtonView(discord.ui.View):
    """Zero-emoji interactive view attached to server verification gate embeds.
    Clicking grants the configured verified role to the interaction user.
    """

    def __init__(self, verified_role_id: int = 0):
        super().__init__(timeout=None)  # Persistent across restarts
        self.verified_role_id = verified_role_id
        if verified_role_id:
            self.verify_button.custom_id = f"ciel_arch_verify:{verified_role_id}"

    @discord.ui.button(
        label="VERIFY ACCESS",
        style=discord.ButtonStyle.primary,
        custom_id="ciel_arch_verify:0"
    )
    async def verify_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await handle_verification_click(interaction, self.verified_role_id)


async def handle_verification_click(interaction: discord.Interaction, fallback_role_id: int = 0):
    """Handles verification role assignment dynamically from custom_id or fallback."""
    guild = interaction.guild
    if not guild:
        await interaction.response.send_message("`[ERROR]` Gate must be activated inside a server.", ephemeral=True)
        return

    role_id = fallback_role_id
    custom_id = interaction.data.get("custom_id", "")
    if custom_id.startswith("ciel_arch_verify:"):
        try:
            parsed_id = int(custom_id.split(":", 1)[1])
            if parsed_id > 0:
                role_id = parsed_id
        except ValueError:
            pass

    role = guild.get_role(role_id)
    if not role:
        await interaction.response.send_message("`[SYSTEM FAULT]` Verification role not found on this server.", ephemeral=True)
        return

    member = interaction.user
    if not isinstance(member, discord.Member):
        await interaction.response.send_message("`[SECURITY]` Failed resolving member identity.", ephemeral=True)
        return

    if role in member.roles:
        await interaction.response.send_message(
            f"`[VERIFIED]` Identity confirmed. You already hold the **{role.name}** clearance.",
            ephemeral=True
        )
        return

    try:
        await member.add_roles(role, reason="Ciel Autonomous Verification Gate Clearance")
        await interaction.response.send_message(
            f"`[ACCESS GRANTED]` Welcome to **{guild.name}**. Verified clearance granted: **{role.name}**.",
            ephemeral=True
        )
    except discord.Forbidden:
        await interaction.response.send_message(
            "`[PERMISSION DENIED]` Bot lacks permission to assign the verification role. Ensure Ciel's role is positioned higher in Server Settings > Roles.",
            ephemeral=True
        )
    except Exception as e:
        logger.error(f"[VERIFY GATE] Failed granting role: {e}")
        await interaction.response.send_message(f"`[ERROR]` Failed assigning clearance: {e}", ephemeral=True)


class ArchitectConfirmationView(discord.ui.View):
    """Two-phase interactive confirmation view for irreversible destructive actions.
    Restricted strictly to the invoking administrator.
    """

    def __init__(self, author_id: int, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.author_id = author_id
        self.value: Optional[bool] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "`[ACCESS DENIED]` Only the administrator who initiated this operation may confirm.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="CONFIRM EXECUTION", style=discord.ButtonStyle.danger, custom_id="ciel_arch_btn_confirm")
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="ABORT OPERATION", style=discord.ButtonStyle.secondary, custom_id="ciel_arch_btn_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        self.stop()
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="`[OPERATION ABORTED]` Destructive command canceled by administrator.",
            view=self
        )

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
