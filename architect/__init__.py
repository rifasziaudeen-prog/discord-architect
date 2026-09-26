"""
architect
=========
Autonomous Discord Server Architect Engine for Ciel.
Provides programmatic declarative blueprints, channel and role management,
native Discord Community Onboarding deployment, and verification systems.
"""

from .service import GuildArchitectService
from .schemas import get_architect_gemini_tools
from .views import VerificationButtonView, ArchitectConfirmationView
from .agent import ArchitectAgent

__all__ = [
    "GuildArchitectService",
    "get_architect_gemini_tools",
    "VerificationButtonView",
    "ArchitectConfirmationView",
    "ArchitectAgent",
]
