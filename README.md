# Project Ciel · Autonomous Server Architect & AI Companion

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-00E5FF.svg)](https://www.python.org/)
[![Discord.py 2.3+](https://img.shields.io/badge/discord.py-2.3+-9D00FF.svg)](https://discordpy.readthedocs.io/)
[![Google GenAI](https://img.shields.io/badge/google--genai-3.1%20flash%20lite-00FF88.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> Autonomous, declarative Discord server scaffolding, native Community Onboarding deployment, and witty conversational AI powered by Google Gemini.

---

## Overview

**Ciel Architect** is an autonomous server engineering bot designed for public deployment. Unlike conventional bots that require manual clicking through Discord settings or hardcoding server IDs in Python scripts, Ciel interprets natural language instructions or declarative blueprints to scaffold channels, configure role hierarchies, deploy verification gates, and orchestrate native **Discord Community Onboarding** workflows.

```
                          [ Administrator Prompt ]
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │ Zero-Token Intent Router     │
                      │ (@Ciel ... / Slash Command) │
                      └──────────────┬──────────────┘
                                     │
                   ┌─────────────────┴─────────────────┐
                   ▼                                   ▼
        [ Architect Sub-Engine ]              [ Conversational AI ]
         • Google GenAI Tools                  • Ciel Anime Persona
         • Dynamic Authority Check             • In-Memory Context
                   │                                   │
                   ▼                                   ▼
        [ Discord REST API ]                  [ Natural Chat Reply ]
         • Declarative Blueprints
         • Native Community Onboarding
         • Two-Phase Confirmation Views
```

---

## Key Features

### 1. Dynamic Authority (Zero Hardcoded IDs)
- **No hardcoded user or guild IDs**: Deployable to any server without touching code.
- **Hierarchical Clearance Matrix**:
  - Global Bot Owner (configured in `.env` or auto-detected from Discord application info).
  - Server Owner (`guild.owner_id`).
  - Discord Administrators (`Administrator` permission).
  - Configurable Architect Role (assigned dynamically via `/setup config role:@Role`).

### 2. Autonomous Declarative Blueprints
- Compile and execute full multi-category, multi-channel server blueprints in seconds.
- Automatically creates role hierarchies with customized hex colors and permission flags.
- Deploys one-click interactive **Verification Gates** and formatted **Server Rules & Guidelines**.

### 3. Native Discord Community Onboarding
- **Audit & Advisory**: Inspects existing onboarding questions, eligibility of default channels, and detects blockers (such as disabled Community settings).
- **Auto-Deployment**: Creates multiple-choice or dropdown questions, resolves or auto-creates assignment roles, and links target channels directly through `guild.edit_onboarding`.

### 4. Zero-Token Intent Interceptor
- Everyday casual conversations with Ciel incur **0 architect tool tokens**.
- Server engineering requests (`@Ciel build a gaming server...`, `@Ciel create a channel...`) are intercepted dynamically via regex and routed directly to the specialized function calling pipeline.

### 5. Two-Phase Safe Confirmation Views
- Irreversible destructive actions (such as mass channel resets or purges) require explicit interactive confirmation through ephemeral, non-delegable button views.

### 6. High-Craft Visual Presentation
- High-contrast glassmorphic palette: Cyber Cyan (`#00E5FF`), Royal Purple (`#9D00FF`), Crimson Warning (`#FF0055`).
- Clean typography and semantic text badges (`[ARCHITECT]`, `[VERIFIED]`, `[SYSTEM]`, `[DEPLOYED]`).

---

## Slash Commands

The bot provides a streamlined, intuitive `/setup` suite alongside quick shortcuts:

| Command | Clearance | Description |
| :--- | :--- | :--- |
| `/setup config [role] [log_channel] [ai_enabled]` | Admins / Owner | Configure architect authority role, audit log channel, and toggle conversational AI. |
| `/setup status` | Everyone | View server telemetry, bot permissions, and Community Onboarding readiness. |
| `/setup blueprint <prompt>` | Architect / Admin | Scaffold a full server layout from natural language (e.g. categories, channels, roles). |
| `/setup onboarding <audit \| configure>` | Architect / Admin | Audit current onboarding status or deploy questions, choices, and default channels. |
| `/setup channel <create \| delete \| edit>` | Architect / Admin | Create, delete, or edit a specific channel or category directly. |
| `/setup role <create \| delete \| assign \| remove>` | Architect / Admin | Create, delete, assign, or remove a server role with custom hex colors. |
| `/setup wipe [keep]` | Architect / Admin | Safely purge channels with interactive two-phase confirmation (preserves rules). |
| `/status` | Everyone | Instant shortcut for `/setup status`. |
| `/ciel <prompt>` | Everyone | Converse with Ciel or issue natural server management directives. |

---

## Natural Language Examples

You can mention `@Ciel` directly in any channel:

- **Server Blueprinting**:
  > `@Ciel build a cyberpunk developer server with announcement, general, dev-lounge, and voice channels.`
- **Channel Mutation**:
  > `@Ciel create a channel named #announcements under Information category.`
- **Role Scaffolding**:
  > `@Ciel create a role named Senior Engineer with color #00E5FF and hoist it.`
- **Community Onboarding**:
  > `@Ciel audit our community onboarding and suggest questions for new members.`
- **Safe Purge**:
  > `@Ciel wipe all channels in this server except #welcome and #general.` *(Presents two-phase confirmation button)*

---

## Quickstart

### Prerequisites
- Python `3.10` or higher
- A Discord Bot Token ([Discord Developer Portal](https://discord.com/developers/applications))
- A Google Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### 1. Clone & Install

```bash
git clone https://github.com/your-username/ciel-architect-bot.git
cd ciel-architect-bot
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```env
# Discord Bot Token
DISCORD_TOKEN=your_discord_bot_token_here

# Google Gemini API Key(s) (comma-separated for failover)
GEMINI_API_KEYS=your_gemini_api_key_here

# Optional Bot Owner ID (auto-detected if blank)
BOT_OWNER_ID=

# Bot Settings
COMMAND_PREFIX=!
DEFAULT_AI_MODEL=gemini-3.1-flash-lite
LOG_LEVEL=INFO
```

### 3. Launch Bot

**On Windows:**
```cmd
start.bat
# or
python main.py
```

**On Linux / macOS:**
```bash
python3 main.py
```

### 4. Required Bot Permissions (Discord Invite)
When generating your bot invite URL in the Discord Developer Portal, ensure the following Bot Permissions are granted:
- `Manage Channels`
- `Manage Roles`
- `Manage Server` (Required for Discord Community Onboarding API)
- `Send Messages` & `Embed Links`
- `Read Message History`
- `Use Application Commands`
- **Privileged Gateway Intents**: Enable **Message Content Intent** and **Server Members Intent**.

---

## Project Structure

```
ciel-architect-bot/
├── .env.example              # Environment configuration template
├── .gitignore                # Git ignore rules
├── LICENSE                   # MIT License
├── README.md                 # Project documentation
├── requirements.txt          # Python dependencies
├── start.bat                 # Windows quick launcher
├── main.py                   # Bot entrypoint, slash command sync
├── config.py                 # Dynamic guild settings & permission store
├── data/
│   └── guild_configs.json    # Persisted per-guild settings (auto-generated)
├── architect/
│   ├── __init__.py
│   ├── agent.py              # Gemini function calling coordinator & embed renderer
│   ├── schemas.py            # Compact Gemini tool function declarations
│   ├── service.py            # Discord REST API automation & onboarding engine
│   └── views.py              # Zero-emoji verification & confirmation views
├── cogs/
│   ├── __init__.py
│   ├── ai_chat.py            # Conversational persona, memory & zero-token router
│   └── architect_commands.py # Streamlined /setup suite, /status, and /ciel commands
└── tests/
    ├── conftest.py
    ├── test_permissions_and_config.py
    ├── test_architect_service.py
    ├── test_community_onboarding.py
    ├── test_schemas.py
    └── test_setup_commands.py
```

---

## Running Unit Tests

Run the full test suite offline without requiring Discord or Gemini credentials:

```bash
pytest tests
```

---

## License

This project is licensed under the [MIT License](LICENSE).
