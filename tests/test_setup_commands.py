"""
tests/test_setup_commands.py
============================
Tests the streamlined /setup slash command group and its subcommands.
"""

import unittest
from unittest.mock import MagicMock
from cogs.architect_commands import SetupCommands


class TestSetupCommands(unittest.TestCase):

    def setUp(self):
        self.mock_bot = MagicMock()
        self.cog = SetupCommands(self.mock_bot)

    def test_setup_group_registered(self):
        """Verifies the /setup group exists and contains all required subcommands."""
        self.assertTrue(hasattr(self.cog, "setup_group"))
        group = self.cog.setup_group
        self.assertEqual(group.name, "setup")

        subcommand_names = [cmd.name for cmd in group.commands]
        expected = ["config", "status", "blueprint", "onboarding", "channel", "role", "wipe"]
        for exp in expected:
            self.assertIn(exp, subcommand_names)

    def test_standalone_shortcuts_registered(self):
        """Verifies standalone /status and /ciel commands are registered."""
        self.assertTrue(hasattr(self.cog, "quick_status_cmd"))
        self.assertTrue(hasattr(self.cog, "ciel_chat_command"))


if __name__ == "__main__":
    unittest.main()
