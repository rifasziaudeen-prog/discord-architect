"""
tests/test_schemas.py
=====================
Tests Gemini function declaration schemas for Discord Server Architect.
"""

import unittest
from architect.schemas import get_architect_gemini_tools


class TestArchitectSchemas(unittest.TestCase):

    def test_schemas_generated_and_names(self):
        """Verifies that all 6 required tools are declared in the schema."""
        tools = get_architect_gemini_tools()
        self.assertGreater(len(tools), 0)

        func_decls = tools[0].function_declarations
        decl_names = [f.name for f in func_decls]

        expected_names = [
            "apply_declarative_blueprint",
            "manage_channel",
            "manage_role",
            "audit_community_onboarding",
            "configure_community_onboarding",
            "wipe_channels_preview"
        ]

        for expected in expected_names:
            self.assertIn(expected, decl_names)


if __name__ == "__main__":
    unittest.main()
