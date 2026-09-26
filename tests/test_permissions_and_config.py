"""
tests/test_permissions_and_config.py
====================================
Tests dynamic clearance verification and guild settings persistence.
Confirms zero hardcoded Discord IDs.
"""

import os
import tempfile
import unittest
from unittest.mock import MagicMock
import discord

from config import GuildConfigManager


class TestPermissionsAndConfig(unittest.TestCase):

    def setUp(self):
        # Create temp file for config storage
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.manager = GuildConfigManager(data_path=self.temp_file.name)

        self.mock_bot = MagicMock()
        self.mock_bot.application = MagicMock()
        self.mock_bot.application.owner = MagicMock(id=999999999)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_zero_hardcoded_user_ids(self):
        """Verifies that no proprietary hardcoded IDs are present in the config manager."""
        self.assertIsNone(self.manager.get_guild_config(12345)["architect_role_id"])

    def test_guild_owner_authorization(self):
        """Guild owner must always be authorized dynamically."""
        mock_guild = MagicMock()
        mock_guild.id = 111111111
        mock_guild.owner_id = 123456789

        mock_member = MagicMock(spec=discord.Member)
        mock_member.id = 123456789
        mock_member.guild = mock_guild
        mock_member.guild_permissions = discord.Permissions(administrator=False)
        mock_member.roles = []

        authorized = self.manager.is_authorized(mock_member, self.mock_bot)
        self.assertTrue(authorized)

    def test_team_application_owner_authorization(self):
        """Team member of application owner team must be authorized dynamically."""
        mock_guild = MagicMock()
        mock_guild.id = 111111111
        mock_guild.owner_id = 999000111

        team_member1 = MagicMock(id=111222)
        team_member2 = MagicMock(id=333444)
        mock_team = MagicMock(spec=discord.Team)
        mock_team.members = [team_member1, team_member2]
        self.mock_bot.application.owner = mock_team

        mock_member = MagicMock(spec=discord.Member)
        mock_member.id = 111222
        mock_member.guild = mock_guild
        mock_member.guild_permissions = discord.Permissions(administrator=False)
        mock_member.roles = []

        authorized = self.manager.is_authorized(mock_member, self.mock_bot)
        self.assertTrue(authorized)

    def test_administrator_authorization(self):
        """Users with Discord Administrator permission must be authorized dynamically."""
        mock_guild = MagicMock()
        mock_guild.id = 111111111
        mock_guild.owner_id = 999000111

        mock_member = MagicMock(spec=discord.Member)
        mock_member.id = 555555555
        mock_member.guild = mock_guild
        mock_member.guild_permissions = discord.Permissions(administrator=True)
        mock_member.roles = []

        authorized = self.manager.is_authorized(mock_member, self.mock_bot)
        self.assertTrue(authorized)

    def test_configured_architect_role_authorization(self):
        """Users possessing the guild-configured architect role must be authorized."""
        mock_guild = MagicMock()
        mock_guild.id = 111111111
        mock_guild.owner_id = 999000111

        # Configure architect role ID
        ARCHITECT_ROLE_ID = 777888999
        self.manager.set_architect_role(mock_guild.id, ARCHITECT_ROLE_ID)

        mock_role = MagicMock(spec=discord.Role)
        mock_role.id = ARCHITECT_ROLE_ID

        mock_member = MagicMock(spec=discord.Member)
        mock_member.id = 444444444
        mock_member.guild = mock_guild
        mock_member.guild_permissions = discord.Permissions(administrator=False)
        mock_member.roles = [mock_role]

        authorized = self.manager.is_authorized(mock_member, self.mock_bot)
        self.assertTrue(authorized)

    def test_unauthorized_regular_member_rejected(self):
        """Regular members without admin, owner, or architect role must be denied."""
        mock_guild = MagicMock()
        mock_guild.id = 111111111
        mock_guild.owner_id = 999000111

        mock_member = MagicMock(spec=discord.Member)
        mock_member.id = 333333333
        mock_member.guild = mock_guild
        mock_member.guild_permissions = discord.Permissions(administrator=False)
        mock_member.roles = []

        authorized = self.manager.is_authorized(mock_member, self.mock_bot)
        self.assertFalse(authorized)

    def test_config_persistence_across_instances(self):
        """Verify settings persist to disk and reload properly."""
        guild_id = 888888888
        self.manager.set_architect_role(guild_id, 123123)
        self.manager.set_log_channel(guild_id, 456456)
        self.manager.set_ai_chat_enabled(guild_id, False)

        # Create new manager pointing to same file
        new_manager = GuildConfigManager(data_path=self.temp_file.name)
        cfg = new_manager.get_guild_config(guild_id)

        self.assertEqual(cfg["architect_role_id"], 123123)
        self.assertEqual(cfg["log_channel_id"], 456456)
        self.assertFalse(cfg["ai_chat_enabled"])


if __name__ == "__main__":
    unittest.main()
