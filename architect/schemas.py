"""
architect/schemas.py
====================
Compact Google GenAI function declarations for Discord Server Architect.
Provides token-efficient schemas for autonomous Discord server management.
"""

from typing import List, Any
import logging

logger = logging.getLogger("architect.schemas")

try:
    from google.genai import types
except ImportError:
    types = None


def get_architect_gemini_tools() -> List[Any]:
    """Builds and returns Google GenAI Tool declarations for the Architect Engine."""
    if not types:
        logger.error("[ARCHITECT SCHEMAS] google.genai.types is not available.")
        return []

    # 1. Declarative Blueprint Execution
    apply_declarative_blueprint_func = types.FunctionDeclaration(
        name="apply_declarative_blueprint",
        description="Compiles and deploys a complete declarative server architecture blueprint (categories, channels, roles, verification, rules).",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "roles": types.Schema(
                    type=types.Type.ARRAY,
                    description="List of roles to scaffold with name, color hex, hoist, and permissions.",
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "name": types.Schema(type=types.Type.STRING),
                            "color": types.Schema(type=types.Type.STRING, description="Hex color (e.g. #00E5FF)"),
                            "hoist": types.Schema(type=types.Type.BOOLEAN),
                            "mentionable": types.Schema(type=types.Type.BOOLEAN),
                            "permissions": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING))
                        },
                        required=["name"]
                    )
                ),
                "categories": types.Schema(
                    type=types.Type.ARRAY,
                    description="Categories to structure.",
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={"name": types.Schema(type=types.Type.STRING)},
                        required=["name"]
                    )
                ),
                "channels": types.Schema(
                    type=types.Type.ARRAY,
                    description="Channels to create under categories.",
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "name": types.Schema(type=types.Type.STRING),
                            "category": types.Schema(type=types.Type.STRING),
                            "type": types.Schema(type=types.Type.STRING, enum=["text", "voice"]),
                            "topic": types.Schema(type=types.Type.STRING),
                            "locked": types.Schema(type=types.Type.BOOLEAN)
                        },
                        required=["name"]
                    )
                ),
                "verification_gate": types.Schema(
                    type=types.Type.OBJECT,
                    description="Optional verification gate specification.",
                    properties={
                        "channel": types.Schema(type=types.Type.STRING),
                        "role": types.Schema(type=types.Type.STRING),
                        "panel_title": types.Schema(type=types.Type.STRING),
                        "panel_description": types.Schema(type=types.Type.STRING)
                    }
                ),
                "rules_deployment": types.Schema(
                    type=types.Type.OBJECT,
                    description="Optional rules codex specification.",
                    properties={
                        "channel": types.Schema(type=types.Type.STRING),
                        "rules": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING)),
                        "description": types.Schema(type=types.Type.STRING)
                    }
                )
            }
        )
    )

    # 2. Channel CRUD
    manage_channel_func = types.FunctionDeclaration(
        name="manage_channel",
        description="Creates, deletes, or modifies a specific channel or category.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "action": types.Schema(type=types.Type.STRING, enum=["create", "delete", "edit"]),
                "name": types.Schema(type=types.Type.STRING, description="Target channel name or ID"),
                "category": types.Schema(type=types.Type.STRING, description="Parent category name"),
                "channel_type": types.Schema(type=types.Type.STRING, enum=["text", "voice"]),
                "topic": types.Schema(type=types.Type.STRING, description="Channel description/topic"),
                "new_name": types.Schema(type=types.Type.STRING, description="New name if renaming")
            },
            required=["action", "name"]
        )
    )

    # 3. Role CRUD
    manage_role_func = types.FunctionDeclaration(
        name="manage_role",
        description="Creates, deletes, assigns, or removes a server role.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "action": types.Schema(type=types.Type.STRING, enum=["create", "delete", "assign", "remove"]),
                "name": types.Schema(type=types.Type.STRING, description="Role name"),
                "color": types.Schema(type=types.Type.STRING, description="Hex color (e.g. #9D00FF)"),
                "hoist": types.Schema(type=types.Type.BOOLEAN, description="Display separately in member list"),
                "target_user": types.Schema(type=types.Type.STRING, description="User name or ID for assign/remove")
            },
            required=["action", "name"]
        )
    )

    # 4. Native Community Onboarding Audit & Advisory
    audit_community_onboarding_func = types.FunctionDeclaration(
        name="audit_community_onboarding",
        description="Inspects the guild's native Discord Community Onboarding readiness, existing prompts, eligible default channels, and returns architectural suggestions.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={}
        )
    )

    # 5. Configure Native Community Onboarding
    configure_community_onboarding_func = types.FunctionDeclaration(
        name="configure_community_onboarding",
        description="Deploys or updates native Discord Community Onboarding questions (single/multi-select, dropdown/multiple-choice), role assignments, and default channels.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "prompts_spec": types.Schema(
                    type=types.Type.ARRAY,
                    description="List of onboarding questions to configure.",
                    items=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "title": types.Schema(type=types.Type.STRING, description="The onboarding question header"),
                            "single_select": types.Schema(type=types.Type.BOOLEAN, description="True for single-choice, False for multi-select"),
                            "required": types.Schema(type=types.Type.BOOLEAN, description="Whether users must answer before joining"),
                            "in_onboarding": types.Schema(type=types.Type.BOOLEAN, description="Show in pre-join flow"),
                            "type": types.Schema(type=types.Type.STRING, enum=["multiple_choice", "dropdown"]),
                            "options": types.Schema(
                                type=types.Type.ARRAY,
                                description="Answer options for this question",
                                items=types.Schema(
                                    type=types.Type.OBJECT,
                                    properties={
                                        "title": types.Schema(type=types.Type.STRING, description="Option label"),
                                        "description": types.Schema(type=types.Type.STRING, description="Subtext explanation"),
                                        "roles": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING), description="Roles assigned upon choosing this option"),
                                        "channels": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING), description="Channels unlocked upon choosing this option")
                                    },
                                    required=["title"]
                                )
                            )
                        },
                        required=["title", "options"]
                    )
                ),
                "default_channels_spec": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(type=types.Type.STRING),
                    description="List of default channel names every new member gets added to."
                ),
                "enabled": types.Schema(type=types.Type.BOOLEAN, description="Whether Onboarding should be active"),
                "mode": types.Schema(type=types.Type.STRING, enum=["default", "advanced"]),
                "auto_create_roles": types.Schema(type=types.Type.BOOLEAN, description="Auto-create missing roles referenced in options")
            },
            required=["prompts_spec"]
        )
    )

    # 6. Mass Channel Wipe Preview
    wipe_channels_preview_func = types.FunctionDeclaration(
        name="wipe_channels_preview",
        description="Generates an irreversible mass channel wipe preview requiring two-phase administrator button confirmation.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "keep_channels": types.Schema(
                    type=types.Type.ARRAY,
                    items=types.Schema(type=types.Type.STRING),
                    description="Channel names or IDs to preserve from deletion."
                )
            }
        )
    )

    return [
        types.Tool(function_declarations=[
            apply_declarative_blueprint_func,
            manage_channel_func,
            manage_role_func,
            audit_community_onboarding_func,
            configure_community_onboarding_func,
            wipe_channels_preview_func
        ])
    ]
