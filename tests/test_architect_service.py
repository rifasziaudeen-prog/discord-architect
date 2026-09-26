"""
tests/test_architect_service.py
===============================
Unit tests for GuildArchitectService methods in Ciel Architect Bot.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import discord

from architect.service import GuildArchitectService


class TestArchitectService(unittest.TestCase):

    def setUp(self):
        self.mock_bot = MagicMock()
        self.service = GuildArchitectService(self.mock_bot)

        self.mock_guild = MagicMock(spec=discord.Guild)
        self.mock_guild.id = 1525583568598732851
        self.mock_guild.name = "Test Nexus"
        self.mock_guild.categories = []
        self.mock_guild.channels = []
        self.mock_guild.roles = []
        self.mock_guild.default_role = MagicMock(spec=discord.Role, name="@everyone")

    def test_parse_color_valid_and_fallback(self):
        """Verifies color parsing handles valid hex strings and fallbacks."""
        c1 = self.service.parse_color("#00E5FF")
        self.assertEqual(c1.value, 0x00E5FF)

        c2 = self.service.parse_color("#9D00FF")
        self.assertEqual(c2.value, 0x9D00FF)

        # Invalid fallback
        c3 = self.service.parse_color("invalid_hex")
        self.assertEqual(c3.value, 0x00E5FF)

    async def asyncSetUp(self):
        pass

    def test_channel_resolution(self):
        """Tests resolving channels by ID, mention, or name."""
        ch1 = MagicMock(spec=discord.TextChannel)
        ch1.id = 1001
        ch1.name = "general"

        ch2 = MagicMock(spec=discord.TextChannel)
        ch2.id = 1002
        ch2.name = "announcements"

        self.mock_guild.channels = [ch1, ch2]
        self.mock_guild.get_channel = lambda cid: ch1 if cid == 1001 else (ch2 if cid == 1002 else None)

        self.assertEqual(self.service.resolve_channel("general", self.mock_guild), ch1)
        self.assertEqual(self.service.resolve_channel("<#1002>", self.mock_guild), ch2)
        self.assertEqual(self.service.resolve_channel(1001, self.mock_guild), ch1)

    def test_role_resolution(self):
        """Tests resolving roles by ID, mention, or name."""
        r1 = MagicMock(spec=discord.Role)
        r1.id = 2001
        r1.name = "Moderator"

        r2 = MagicMock(spec=discord.Role)
        r2.id = 2002
        r2.name = "Verified"

        self.mock_guild.roles = [r1, r2]
        self.mock_guild.get_role = lambda rid: r1 if rid == 2001 else (r2 if rid == 2002 else None)

        self.assertEqual(self.service.resolve_role("moderator", self.mock_guild), r1)
        self.assertEqual(self.service.resolve_role("<@&2002>", self.mock_guild), r2)
        self.assertEqual(self.service.resolve_role(2001, self.mock_guild), r1)


class TestArchitectServiceAsync(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_bot = MagicMock()
        self.service = GuildArchitectService(self.mock_bot)

        self.mock_guild = MagicMock(spec=discord.Guild)
        self.mock_guild.id = 999111
        self.mock_guild.name = "Async Guild"
        self.mock_guild.categories = []
        self.mock_guild.channels = []
        self.mock_guild.roles = []
        self.mock_guild.default_role = MagicMock(spec=discord.Role, name="@everyone")

    async def test_manage_channel_create(self):
        """Tests channel creation through service."""
        mock_channel = MagicMock(spec=discord.TextChannel, id=777)
        mock_channel.name = "lobby"
        self.mock_guild.create_text_channel = AsyncMock(return_value=mock_channel)

        res = await self.service.manage_channel(
            self.mock_guild,
            action="create",
            name="lobby",
            channel_type="text"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["channel_name"], "lobby")
        self.mock_guild.create_text_channel.assert_awaited_once()

    async def test_manage_role_create(self):
        """Tests role creation through service."""
        mock_role = MagicMock(spec=discord.Role, id=888)
        mock_role.name = "Architect"
        self.mock_guild.create_role = AsyncMock(return_value=mock_role)

        res = await self.service.manage_role(
            self.mock_guild,
            action="create",
            name="Architect",
            color="#00E5FF"
        )
        self.assertTrue(res["success"])
        self.assertEqual(res["role_name"], "Architect")
        self.mock_guild.create_role.assert_awaited_once()

    async def test_wipe_simulation(self):
        """Tests safe wipe preview calculation without executing deletion."""
        ch1 = MagicMock(spec=discord.TextChannel, id=1)
        ch1.name = "general"
        ch2 = MagicMock(spec=discord.TextChannel, id=2)
        ch2.name = "bot-commands"
        ch3 = MagicMock(spec=discord.TextChannel, id=3)
        ch3.name = "keep-me"

        self.mock_guild.channels = [ch1, ch2, ch3]

        preview = await self.service.wipe_server_channels(
            self.mock_guild,
            keep_channels=["keep-me"],
            simulate=True
        )
        self.assertTrue(preview["simulate"])
        self.assertEqual(preview["channels_count"], 2)
        self.assertIn("general", preview["channels"])
        self.assertNotIn("keep-me", preview["channels"])


if __name__ == "__main__":
    unittest.main()
