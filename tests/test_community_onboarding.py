"""
tests/test_community_onboarding.py
==================================
Unit tests for Community Onboarding audit and configuration in Discord Server Architect.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock
import discord

from architect.service import GuildArchitectService


class TestCommunityOnboarding(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_bot = MagicMock()
        self.service = GuildArchitectService(self.mock_bot)

        self.mock_guild = MagicMock(spec=discord.Guild)
        self.mock_guild.id = 888999
        self.mock_guild.name = "Community Matrix"
        self.mock_guild.features = ["COMMUNITY"]
        self.mock_guild.default_role = MagicMock(spec=discord.Role, name="@everyone")
        self.mock_guild.roles = []
        self.mock_guild.text_channels = []

    async def test_audit_non_community_server(self):
        """Verifies that non-community servers report the Community blocker clearly."""
        self.mock_guild.features = []

        report = await self.service.audit_community_onboarding(self.mock_guild)
        self.assertFalse(report["community_enabled"])
        self.assertTrue(any("Community is DISABLED" in b for b in report["blockers"]))

    async def test_audit_community_server_ready(self):
        """Verifies auditing an active community server with default channels."""
        ch = MagicMock(spec=discord.TextChannel)
        ch.name = "welcome-chat"
        perms = MagicMock(view_channel=True, read_messages=True)
        ch.permissions_for.return_value = perms
        self.mock_guild.text_channels = [ch]

        mock_onboarding = MagicMock()
        mock_onboarding.enabled = True
        mock_onboarding.prompts = []
        self.mock_guild.onboarding = AsyncMock(return_value=mock_onboarding)

        report = await self.service.audit_community_onboarding(self.mock_guild)
        self.assertTrue(report["community_enabled"])
        self.assertTrue(report["onboarding_active"])
        self.assertIn("welcome-chat", report["candidate_default_channels"])

    async def test_configure_community_onboarding(self):
        """Verifies compiling and deploying onboarding prompts to Discord API."""
        self.mock_guild.edit_onboarding = AsyncMock()

        prompts_spec = [
            {
                "title": "Select your primary interest",
                "single_select": True,
                "required": True,
                "in_onboarding": True,
                "type": "multiple_choice",
                "options": [
                    {
                        "title": "Development",
                        "description": "Access coding channels",
                        "roles": ["Developer"]
                    },
                    {
                        "title": "Gaming",
                        "description": "Access gaming lounges",
                        "roles": ["Gamer"]
                    }
                ]
            }
        ]

        # Setup auto-create role mock
        dev_role = MagicMock(spec=discord.Role, name="Developer")
        gamer_role = MagicMock(spec=discord.Role, name="Gamer")
        self.mock_guild.create_role = AsyncMock(side_effect=[dev_role, gamer_role])

        res = await self.service.configure_community_onboarding(
            self.mock_guild,
            prompts_spec=prompts_spec,
            auto_create_roles=True
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["prompts_count"], 1)
        self.mock_guild.edit_onboarding.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
