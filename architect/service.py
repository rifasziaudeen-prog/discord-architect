"""
architect/service.py
====================
Programmatic Discord server automation service for Ciel Architect Bot.
Executes declarative blueprints, channel and role CRUD, native Discord Community Onboarding,
verification gates, and server guides. Zero hardcoded IDs.
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Union

import discord
from discord.ext import commands

from config import COLOR_CYAN, COLOR_PURPLE, COLOR_DANGER, COLOR_SUCCESS

logger = logging.getLogger("ciel.architect.service")


class GuildArchitectService:
    """Core programmatic automation engine interfacing with Discord API."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def parse_color(hex_val: Optional[str]) -> discord.Color:
        """Parses a hex color string into discord.Color, falling back to Cyan."""
        if not hex_val:
            return discord.Color.from_str(COLOR_CYAN)
        clean = hex_val.strip().lstrip("#")
        try:
            return discord.Color(int(clean, 16))
        except ValueError:
            return discord.Color.from_str(COLOR_CYAN)

    def resolve_category(self, identifier: Union[int, str], guild: discord.Guild) -> Optional[discord.CategoryChannel]:
        """Resolves a category by numeric ID or exact/case-insensitive name."""
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            cat = guild.get_channel(int(identifier))
            if isinstance(cat, discord.CategoryChannel):
                return cat

        ident_str = str(identifier).strip().lower()
        for cat in guild.categories:
            if cat.name.lower() == ident_str:
                return cat
        for cat in guild.categories:
            if ident_str in cat.name.lower():
                return cat
        return None

    def resolve_channel(self, identifier: Union[int, str], guild: discord.Guild) -> Optional[discord.abc.GuildChannel]:
        """Resolves a channel by numeric ID, mention, or name."""
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            ch = guild.get_channel(int(identifier))
            if ch:
                return ch

        ident_str = str(identifier).strip().lstrip("#").lower()
        mention_match = re.search(r'<#(\d+)>', str(identifier))
        if mention_match:
            ch = guild.get_channel(int(mention_match.group(1)))
            if ch:
                return ch

        for ch in guild.channels:
            if ch.name.lower() == ident_str:
                return ch
        return None

    def resolve_role(self, identifier: Union[int, str], guild: discord.Guild) -> Optional[discord.Role]:
        """Resolves a role by numeric ID, mention, or name."""
        if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
            role = guild.get_role(int(identifier))
            if role:
                return role

        ident_str = str(identifier).strip().lstrip("@").lower()
        mention_match = re.search(r'<@&(\d+)>', str(identifier))
        if mention_match:
            role = guild.get_role(int(mention_match.group(1)))
            if role:
                return role

        for r in guild.roles:
            if r.name.lower() == ident_str:
                return r
        for r in guild.roles:
            if ident_str in r.name.lower() and r.name != "@everyone":
                return r
        return None

    # ── 1. DECLARATIVE BLUEPRINT SCAFFOLDING ──────────────────────────
    async def apply_declarative_blueprint(
        self,
        guild: discord.Guild,
        blueprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compiles and executes a declarative server blueprint.
        Includes role hierarchies, categories, channels, permissions, and verification gates.
        """
        stages_executed = []
        errors = []

        # Stage 1: Role Genesis
        roles_spec = blueprint.get("roles", [])
        created_roles: Dict[str, discord.Role] = {}

        if roles_spec:
            try:
                for r_info in roles_spec:
                    name = r_info.get("name")
                    if not name:
                        continue
                    existing = self.resolve_role(name, guild)
                    if existing:
                        created_roles[name] = existing
                        continue

                    color = self.parse_color(r_info.get("color"))
                    hoist = bool(r_info.get("hoist", False))
                    mentionable = bool(r_info.get("mentionable", False))

                    perms = discord.Permissions.none()
                    if r_info.get("permissions"):
                        try:
                            perms = discord.Permissions(**{p: True for p in r_info["permissions"]})
                        except Exception as p_err:
                            errors.append(f"Permissions for role '{name}': {p_err}")

                    new_role = await guild.create_role(
                        name=name,
                        color=color,
                        hoist=hoist,
                        mentionable=mentionable,
                        permissions=perms,
                        reason="Ciel Blueprint Scaffolding"
                    )
                    created_roles[name] = new_role
                    await asyncio.sleep(0.4)

                stages_executed.append(f"Role Hierarchy ({len(roles_spec)} roles processed)")
            except Exception as e:
                errors.append(f"Role Genesis Error: {e}")

        # Stage 2: Channel & Category Layout
        categories_spec = blueprint.get("categories", [])
        channels_spec = blueprint.get("channels", [])

        if categories_spec or channels_spec:
            try:
                cat_map: Dict[str, discord.CategoryChannel] = {}

                # Create Categories
                for cat_info in categories_spec:
                    c_name = cat_info.get("name")
                    if not c_name:
                        continue
                    cat_obj = self.resolve_category(c_name, guild)
                    if not cat_obj:
                        cat_obj = await guild.create_category(
                            name=c_name,
                            reason="Ciel Blueprint Scaffolding"
                        )
                        await asyncio.sleep(0.3)
                    cat_map[c_name] = cat_obj

                # Create Channels
                created_count = 0
                for ch_info in channels_spec:
                    ch_name = ch_info.get("name")
                    if not ch_name:
                        continue
                    ch_type = ch_info.get("type", "text").lower()
                    target_cat = cat_map.get(ch_info.get("category", "")) or self.resolve_category(ch_info.get("category", ""), guild)
                    topic = ch_info.get("topic")

                    overwrites = {}
                    if ch_info.get("locked"):
                        overwrites[guild.default_role] = discord.PermissionOverwrite(send_messages=False, add_reactions=False)

                    if ch_type == "voice":
                        await guild.create_voice_channel(
                            name=ch_name,
                            category=target_cat,
                            overwrites=overwrites,
                            reason="Ciel Blueprint Scaffolding"
                        )
                    else:
                        await guild.create_text_channel(
                            name=ch_name,
                            category=target_cat,
                            topic=topic,
                            overwrites=overwrites,
                            reason="Ciel Blueprint Scaffolding"
                        )
                    created_count += 1
                    await asyncio.sleep(0.3)

                stages_executed.append(f"Channel Infrastructure ({created_count} channels structured)")
            except Exception as e:
                errors.append(f"Channel Infrastructure Error: {e}")

        # Stage 3: Verification Gate
        if blueprint.get("verification_gate"):
            v_spec = blueprint["verification_gate"]
            channel_name = v_spec.get("channel", "verification")
            target_ch = self.resolve_channel(channel_name, guild)
            role_name = v_spec.get("role", "Verified")
            target_role = created_roles.get(role_name) or self.resolve_role(role_name, guild)

            if target_ch and isinstance(target_ch, discord.TextChannel) and target_role:
                try:
                    await self.deploy_verification_gate(
                        channel=target_ch,
                        verified_role=target_role,
                        panel_title=v_spec.get("panel_title"),
                        panel_description=v_spec.get("panel_description")
                    )
                    stages_executed.append(f"Verification Matrix (Channel: #{target_ch.name})")
                except Exception as ve:
                    errors.append(f"Verification Gate Error: {ve}")

        # Stage 4: Server Guide & Rules
        if blueprint.get("rules_deployment"):
            r_spec = blueprint["rules_deployment"]
            ch_name = r_spec.get("channel", "rules")
            rules_ch = self.resolve_channel(ch_name, guild)
            if rules_ch and isinstance(rules_ch, discord.TextChannel):
                try:
                    await self.deploy_server_guide_and_rules(
                        channel=rules_ch,
                        rules_list=r_spec.get("rules", []),
                        server_description=r_spec.get("description")
                    )
                    stages_executed.append(f"Rules & Codex Deployment (#{rules_ch.name})")
                except Exception as re_err:
                    errors.append(f"Rules Deployment Error: {re_err}")

        return {
            "success": len(errors) == 0,
            "guild_id": str(guild.id),
            "guild_name": guild.name,
            "stages_executed": stages_executed,
            "errors": errors
        }

    # ── 2. INDIVIDUAL CHANNEL CRUD ────────────────────────────────────
    async def manage_channel(
        self,
        guild: discord.Guild,
        action: str,
        name: str,
        category: Optional[str] = None,
        channel_type: str = "text",
        topic: Optional[str] = None,
        new_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Performs atomic channel mutation: create, delete, edit."""
        act = action.lower().strip()
        ch_type = channel_type.lower().strip()

        try:
            if act == "create":
                target_cat = self.resolve_category(category, guild) if category else None
                if ch_type == "voice":
                    ch = await guild.create_voice_channel(
                        name=name,
                        category=target_cat,
                        reason="Ciel Channel Mutation"
                    )
                else:
                    ch = await guild.create_text_channel(
                        name=name,
                        category=target_cat,
                        topic=topic,
                        reason="Ciel Channel Mutation"
                    )
                return {"success": True, "action": "created", "channel_id": str(ch.id), "channel_name": ch.name}

            elif act == "delete":
                target_ch = self.resolve_channel(name, guild)
                if not target_ch:
                    return {"success": False, "error": f"Channel '{name}' not found."}
                old_name = target_ch.name
                await target_ch.delete(reason="Ciel Channel Mutation")
                return {"success": True, "action": "deleted", "channel_name": old_name}

            elif act == "edit":
                target_ch = self.resolve_channel(name, guild)
                if not target_ch:
                    return {"success": False, "error": f"Channel '{name}' not found."}

                kwargs = {}
                if new_name:
                    kwargs["name"] = new_name
                if topic and isinstance(target_ch, discord.TextChannel):
                    kwargs["topic"] = topic
                if category:
                    target_cat = self.resolve_category(category, guild)
                    if target_cat:
                        kwargs["category"] = target_cat

                if kwargs:
                    await target_ch.edit(**kwargs, reason="Ciel Channel Mutation")
                return {"success": True, "action": "edited", "channel_name": target_ch.name}

            return {"success": False, "error": f"Unknown action '{action}'."}
        except discord.Forbidden:
            return {"success": False, "error": "Bot lacks permissions to manage channels."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── 3. INDIVIDUAL ROLE CRUD ───────────────────────────────────────
    async def manage_role(
        self,
        guild: discord.Guild,
        action: str,
        name: str,
        color: Optional[str] = None,
        hoist: bool = False,
        target_user: Optional[str] = None
    ) -> Dict[str, Any]:
        """Performs atomic role mutation: create, delete, assign, remove."""
        act = action.lower().strip()

        try:
            if act == "create":
                existing = self.resolve_role(name, guild)
                if existing:
                    return {"success": True, "action": "already_exists", "role_id": str(existing.id), "role_name": existing.name}

                c = self.parse_color(color)
                role = await guild.create_role(
                    name=name,
                    color=c,
                    hoist=hoist,
                    reason="Ciel Role Mutation"
                )
                return {"success": True, "action": "created", "role_id": str(role.id), "role_name": role.name}

            elif act == "delete":
                role = self.resolve_role(name, guild)
                if not role:
                    return {"success": False, "error": f"Role '{name}' not found."}
                r_name = role.name
                await role.delete(reason="Ciel Role Mutation")
                return {"success": True, "action": "deleted", "role_name": r_name}

            elif act in ("assign", "remove"):
                if not target_user:
                    return {"success": False, "error": "A target user must be specified for assign/remove."}
                role = self.resolve_role(name, guild)
                if not role:
                    return {"success": False, "error": f"Role '{name}' not found."}

                user_id_match = re.search(r'(\d+)', target_user)
                member = guild.get_member(int(user_id_match.group(1))) if user_id_match else None
                if not member:
                    member = discord.utils.find(lambda m: m.name.lower() == target_user.lower(), guild.members)
                if not member:
                    return {"success": False, "error": f"Member '{target_user}' could not be resolved."}

                if act == "assign":
                    await member.add_roles(role, reason="Ciel Role Assignment")
                    return {"success": True, "action": "assigned", "role_name": role.name, "user": member.display_name}
                else:
                    await member.remove_roles(role, reason="Ciel Role Removal")
                    return {"success": True, "action": "removed", "role_name": role.name, "user": member.display_name}

            return {"success": False, "error": f"Unknown action '{action}'."}
        except discord.Forbidden:
            return {"success": False, "error": "Bot lacks permissions or role hierarchy is too low to modify this role."}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── 4. NATIVE DISCORD COMMUNITY ONBOARDING ────────────────────────
    async def audit_community_onboarding(self, guild: discord.Guild) -> Dict[str, Any]:
        """Audits the guild's native Discord Community Onboarding readiness and status."""
        has_community = "COMMUNITY" in guild.features
        blockers = []
        suggestions = []

        if not has_community:
            blockers.append("Server Feature: Community is DISABLED. Enable via Server Settings > Enable Community.")

        current_prompts = []
        is_enabled = False
        mode_str = "default"

        if has_community:
            try:
                onboarding = await guild.onboarding()
                is_enabled = onboarding.enabled
                mode_str = str(onboarding.mode.name) if hasattr(onboarding, "mode") else "default"

                for p in onboarding.prompts:
                    opts = []
                    for o in p.options:
                        opts.append({
                            "title": o.title,
                            "description": o.description,
                            "roles": [r.name for r in getattr(o, "roles", [])],
                            "channels": [c.name for c in getattr(o, "channels", [])]
                        })
                    current_prompts.append({
                        "id": str(p.id),
                        "title": p.title,
                        "single_select": p.single_select,
                        "required": p.required,
                        "in_onboarding": p.in_onboarding,
                        "type": str(p.type.name),
                        "options": opts
                    })
            except discord.Forbidden:
                blockers.append("Permission Denied: Bot requires 'Manage Server' to inspect Onboarding.")
            except discord.HTTPException as http_err:
                blockers.append(f"Discord API Onboarding Query Error: {http_err}")
            except Exception as e:
                blockers.append(f"Onboarding Audit Error: {e}")

        # Eligible default channels check
        eligible_default_channels = []
        for ch in guild.text_channels:
            perms = ch.permissions_for(guild.default_role)
            if perms.view_channel and perms.read_messages:
                eligible_default_channels.append(ch.name)

        if len(eligible_default_channels) < 1:
            blockers.append("Onboarding Rule: At least 1 public channel visible to @everyone is required as a default channel.")

        # Architectural suggestions
        if len(current_prompts) == 0:
            suggestions.append("Identity Question: Add a prompt asking members for their primary interest or pronouns.")
            suggestions.append("Notification Opt-In: Add a prompt letting members select notification roles (e.g. @Announcements, @Events).")

        return {
            "guild_id": str(guild.id),
            "guild_name": guild.name,
            "community_enabled": has_community,
            "onboarding_active": is_enabled,
            "onboarding_mode": mode_str,
            "current_prompts": current_prompts,
            "candidate_default_channels": eligible_default_channels[:8],
            "blockers": blockers,
            "suggestions": suggestions
        }

    async def configure_community_onboarding(
        self,
        guild: discord.Guild,
        prompts_spec: List[Dict[str, Any]],
        default_channels_spec: Optional[List[str]] = None,
        enabled: bool = True,
        mode: str = "default",
        auto_create_roles: bool = True
    ) -> Dict[str, Any]:
        """Compiles and deploys native Discord Community Onboarding questions and options."""
        if "COMMUNITY" not in guild.features:
            return {
                "success": False,
                "error": "Guild does not have the 'COMMUNITY' feature enabled in Server Settings."
            }

        if not hasattr(guild, "edit_onboarding"):
            return {
                "success": False,
                "error": "Current discord.py version does not support edit_onboarding."
            }

        default_channels = []
        if default_channels_spec:
            for ch_query in default_channels_spec:
                ch = self.resolve_channel(ch_query, guild)
                if ch and ch not in default_channels:
                    default_channels.append(ch)

        if not default_channels:
            for ch in getattr(guild, "text_channels", []):
                perms = ch.permissions_for(guild.default_role)
                if getattr(perms, "view_channel", False):
                    default_channels.append(ch)
            default_channels = default_channels[:5]

        compiled_prompts = []
        created_roles = []
        failed_items = []

        onboarding_mode = discord.OnboardingMode.advanced if str(mode).lower() == "advanced" else discord.OnboardingMode.default

        for p_idx, p_spec in enumerate(prompts_spec):
            title = str(p_spec.get("title", f"Question {p_idx+1}")).strip()
            single_select = bool(p_spec.get("single_select", True))
            required = bool(p_spec.get("required", True))
            in_onboarding = bool(p_spec.get("in_onboarding", True))
            prompt_type = discord.OnboardingPromptType.dropdown if str(p_spec.get("type", "")).lower() == "dropdown" else discord.OnboardingPromptType.multiple_choice

            options_spec = p_spec.get("options", [])
            compiled_options = []

            for opt_spec in options_spec:
                opt_title = str(opt_spec.get("title", "Option")).strip()
                opt_desc = opt_spec.get("description")

                target_roles = []
                for r_name in opt_spec.get("roles", []):
                    role = self.resolve_role(r_name, guild)
                    if not role and auto_create_roles:
                        try:
                            role = await guild.create_role(
                                name=str(r_name).strip(),
                                color=self.parse_color("#9AA5B1"),
                                reason="Ciel Autonomous Onboarding Role Genesis"
                            )
                            created_roles.append(role.name)
                            await asyncio.sleep(0.3)
                        except Exception as r_err:
                            logger.warning(f"[ONBOARDING] Auto-create role '{r_name}' failed: {r_err}")
                    if role and role not in target_roles:
                        target_roles.append(role)

                target_channels = []
                for c_name in opt_spec.get("channels", []):
                    ch = self.resolve_channel(c_name, guild)
                    if ch and ch not in target_channels:
                        target_channels.append(ch)

                try:
                    prompt_opt = discord.OnboardingPromptOption(
                        title=opt_title,
                        description=opt_desc,
                        roles=target_roles if target_roles else discord.utils.MISSING,
                        channels=target_channels if target_channels else discord.utils.MISSING
                    )
                    compiled_options.append(prompt_opt)
                except Exception as opt_err:
                    failed_items.append(f"Option '{opt_title}': {opt_err}")

            if len(compiled_options) < 2:
                failed_items.append(f"Prompt '{title}': Discord API requires at least 2 options for an onboarding prompt (compiled {len(compiled_options)}).")
                continue

            try:
                prompt_obj = discord.OnboardingPrompt(
                    type=prompt_type,
                    title=title,
                    options=compiled_options,
                    single_select=single_select,
                    required=required,
                    in_onboarding=in_onboarding
                )
                compiled_prompts.append(prompt_obj)
            except Exception as p_err:
                failed_items.append(f"Prompt '{title}': {p_err}")

        if not compiled_prompts:
            return {
                "success": False,
                "error": "No valid onboarding prompts could be compiled.",
                "details": failed_items
            }

        try:
            await guild.edit_onboarding(
                prompts=compiled_prompts,
                default_channels=default_channels if default_channels else discord.utils.MISSING,
                enabled=enabled,
                mode=onboarding_mode,
                reason="Ciel Autonomous Community Onboarding Deployment"
            )
            return {
                "success": True,
                "guild_id": str(guild.id),
                "guild_name": guild.name,
                "prompts_count": len(compiled_prompts),
                "default_channels_count": len(default_channels),
                "auto_created_roles": created_roles,
                "enabled": enabled,
                "mode": str(mode)
            }
        except discord.Forbidden:
            return {
                "success": False,
                "error": "Permission Denied: Ciel requires 'Manage Server' and 'Manage Roles' to configure onboarding."
            }
        except discord.HTTPException as http_err:
            return {
                "success": False,
                "error": f"Discord API HTTP Error: {getattr(http_err, 'text', None) or http_err}"
            }
        except Exception as err:
            return {
                "success": False,
                "error": f"Failed configuring onboarding: {err}"
            }

    # ── 5. VERIFICATION GATE DEPLOYMENT ───────────────────────────────
    async def deploy_verification_gate(
        self,
        channel: discord.TextChannel,
        verified_role: discord.Role,
        panel_title: Optional[str] = None,
        panel_description: Optional[str] = None
    ) -> discord.Message:
        """Deploys an interactive verification gate embed with button view."""
        from .views import VerificationButtonView

        title = panel_title or f"[GATEWAY] Welcome to {channel.guild.name}"
        desc = panel_description or (
            f"Click the button below to complete verification and gain access to the server.\n\n"
            f"• Clearance Granted: **@{verified_role.name}**\n"
            f"• Enforces server integrity and automated security."
        )

        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color.from_str(COLOR_CYAN)
        )
        embed.set_footer(text="Ciel Security Matrix • One-Click Verification Gate")

        view = VerificationButtonView(verified_role.id)
        msg = await channel.send(embed=embed, view=view)
        return msg

    # ── 6. SERVER GUIDE & RULES ───────────────────────────────────────
    async def deploy_server_guide_and_rules(
        self,
        channel: discord.TextChannel,
        rules_list: List[str],
        server_description: Optional[str] = None
    ) -> discord.Message:
        """Publishes clean, glassmorphic server rules and community codex."""
        guild = channel.guild
        title = f"[SERVER CODEX] {guild.name}"
        desc = server_description or f"Welcome to {guild.name}. Please review our community standards below."

        embed = discord.Embed(
            title=title,
            description=desc,
            color=discord.Color.from_str(COLOR_PURPLE)
        )

        if not rules_list:
            rules_list = [
                "Respect all community members. Harassment, hate speech, and toxicity will not be tolerated.",
                "Keep discussions relevant to the appropriate channels.",
                "No unsolicited self-promotion, advertising, or spam.",
                "Adhere to Discord Terms of Service and Community Guidelines."
            ]

        for idx, rule in enumerate(rules_list, 1):
            embed.add_field(
                name=f"RULE {idx:02d}",
                value=f"✦ {rule}",
                inline=False
            )

        embed.set_footer(text="Ciel Autonomous Architect • Community Standards")
        return await channel.send(embed=embed)

    # ── 7. MASS CHANNEL WIPE (WITH SAFETY PREVIEW) ────────────────────
    async def wipe_server_channels(
        self,
        guild: discord.Guild,
        keep_channels: Optional[List[str]] = None,
        simulate: bool = True
    ) -> Dict[str, Any]:
        """Safely wipes channels with preview support and preservation filters.
        Automatically protects Community-mandated channels (rules_channel, public_updates_channel).
        """
        keep_set = {str(k).strip().lower().lstrip("#") for k in (keep_channels or [])}

        # Automatically protect Community-mandated channels
        protected_ids = set()
        protected_names = []
        if getattr(guild, "rules_channel", None) and guild.rules_channel:
            protected_ids.add(guild.rules_channel.id)
            protected_names.append(f"#{guild.rules_channel.name} (Community Rules)")
        if getattr(guild, "public_updates_channel", None) and guild.public_updates_channel:
            protected_ids.add(guild.public_updates_channel.id)
            protected_names.append(f"#{guild.public_updates_channel.name} (Community Updates)")

        targets: List[discord.abc.GuildChannel] = []
        for ch in guild.channels:
            if ch.id in protected_ids:
                continue
            if ch.name.lower() in keep_set or str(ch.id) in keep_set:
                continue
            targets.append(ch)

        if simulate:
            return {
                "simulate": True,
                "channels_count": len(targets),
                "channels": [c.name for c in targets[:25]],
                "protected_community_channels": protected_names
            }

        deleted_count = 0
        errors = []

        # Delete text/voice channels first
        for ch in targets:
            if not isinstance(ch, discord.CategoryChannel):
                try:
                    await ch.delete(reason="Ciel Mass Channel Purge")
                    deleted_count += 1
                    await asyncio.sleep(0.3)
                except Exception as e:
                    errors.append(f"#{ch.name}: {e}")

        # Delete categories second
        for ch in targets:
            if isinstance(ch, discord.CategoryChannel):
                try:
                    await ch.delete(reason="Ciel Mass Category Purge")
                    deleted_count += 1
                    await asyncio.sleep(0.3)
                except Exception as e:
                    errors.append(f"Category '{ch.name}': {e}")

        return {
            "simulate": False,
            "deleted_count": deleted_count,
            "errors": errors
        }
