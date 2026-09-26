# Setup & Deployment Guide · Project Ciel

> Step-by-step setup guide for configuring, deploying, and self-hosting Ciel Architect Bot.

---

## 1. Discord Developer Portal Setup

### Step 1.1: Create Application
1. Navigate to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** in the top-right corner.
3. Enter a name (e.g., `Ciel` or `Ciel Architect`) and confirm.

### Step 1.2: Configure Bot User
1. Select the **Bot** tab on the left sidebar.
2. Click **Reset Token** to copy your **Discord Bot Token**. Keep this token private.
3. Under **Privileged Gateway Intents**, enable:
   - **Presence Intent** (Optional)
   - **Server Members Intent** (Required for role assignments and diagnostics)
   - **Message Content Intent** (Required for reading mentions and natural commands)
4. Click **Save Changes**.

### Step 1.3: Generate Bot Invite URL
1. Go to **OAuth2 > URL Generator**.
2. Under **Scopes**, select:
   - `bot`
   - `applications.commands`
3. Under **Bot Permissions**, select:
   - `Manage Channels`
   - `Manage Roles`
   - `Manage Server` (Mandatory for Community Onboarding)
   - `Send Messages`
   - `Embed Links`
   - `Attach Files`
   - `Read Message History`
   - `Use Application Commands`
4. Copy the generated URL and open it in your browser to invite Ciel to your server.

---

## 2. Google Gemini API Setup

1. Visit [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google account.
3. Click **Get API key** and create a new key.
4. Copy the key. *(Optional: You can create multiple keys for multi-key automatic failover).*

---

## 3. Local Installation & Configuration

### Step 3.1: Clone and Dependencies
```bash
git clone https://github.com/your-username/ciel-architect-bot.git
cd ciel-architect-bot
pip install -r requirements.txt
```

### Step 3.2: Configure `.env`
Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your values:

```env
# Discord Token from Step 1.2
DISCORD_TOKEN=your_discord_bot_token_here

# Gemini API Key from Step 2 (comma-separated if multiple)
GEMINI_API_KEYS=your_gemini_api_key_here

# Optional: Global Bot Owner ID (auto-detected if blank)
BOT_OWNER_ID=

# Bot defaults
COMMAND_PREFIX=!
DEFAULT_AI_MODEL=gemini-2.5-flash
LOG_LEVEL=INFO
```

---

## 4. Launching Ciel

### On Windows
Double-click `start.bat` or run:
```cmd
python main.py
```

### On Linux / macOS
```bash
python3 main.py
```

Upon successful startup, the console displays:
```
================================================================
  PROJECT CIEL · AUTONOMOUS SERVER ARCHITECT
================================================================
  Status      : ONLINE
  Bot Identity: Ciel#0000 (ID: ...)
  Application : Ciel
  Owner       : YourAccount (ID: ...)
  Guilds      : 1 connected
  Latency     : 42.15 ms
  Design      : Glassmorphic Cyberpunk (Zero-Emoji Compliant)
================================================================
```

---

## 5. Server Onboarding & First-Time Setup

### Step 5.1: Verify Permissions
In your server, run:
```
/status
# or
/setup status
```
Check that **Bot Authority Diagnostics** reports `GRANTED` for all three core permissions:
- `Manage Channels`
- `Manage Roles`
- `Manage Server`

> [!IMPORTANT]
> **Role Hierarchy Position**: In Discord **Server Settings > Roles**, drag Ciel's bot role to the top of the role list (just below Owner/Admin). Discord prevents bots from creating, modifying, or assigning roles that are positioned above their own highest role.

### Step 5.2: Configure Server Settings
Optionally assign an architect role and an audit log channel:
```
/setup config role:@Architect log_channel:#audit-logs ai_enabled:True
```

### Step 5.3: Test Scaffolding
Try building a sample server category or full blueprint:
```
/setup blueprint prompt:minimalist developer hub with announcements, dev-chat, and voice-lounge
```
Or mention Ciel in chat:
```
@Ciel build a cyberpunk gaming community with welcome, rules, and voice lounges
```

---

## 6. Troubleshooting & Common Pitfalls

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **`Permission Denied: Missing Manage Server`** | Bot was invited without `Manage Server`. | Re-invite the bot with `Manage Server` or grant it in server settings. |
| **`Cannot modify role`** | Ciel's role is lower than the target role. | Move Ciel's role higher in Server Settings > Roles. |
| **`Community feature is DISABLED`** | Server is a standard Discord server. | Go to Server Settings > Enable Community to use native Onboarding. |
| **`Interaction Timed Out`** | LLM latency exceeded timeout before ACK. | Built-in deferral prevents this; check network connection to Google API. |
| **`Prompt must have at least 2 options`** | Discord API Onboarding constraint. | Ciel enforces this automatically; ensure questions have multiple choices. |
