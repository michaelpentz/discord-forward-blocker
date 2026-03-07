# Discord Forward Blocker

A lightweight Discord bot that silently deletes forwarded messages originating from protected channels and logs them to a designated mod channel.

Discord doesn't natively prevent users from forwarding messages out of specific channels. This bot fills that gap — useful for media-only channels, announcement channels, or any channel where the content shouldn't be redistributed into general conversation threads.

---

## How It Works

When a user forwards a message from a protected channel into any other channel, the bot:

1. **Silently deletes** the forwarded message
2. **Posts a log embed** to your designated mod channel

```
🗑️ Forward Blocked
━━━━━━━━━━━━━━━━━━━━━━━
  User     @username
  From     #food (protected)
  To       #general
  Message  "check this out" 🖼️
━━━━━━━━━━━━━━━━━━━━━━━
  March 7, 2026 at 11:32 AM
```

Regular replies, non-forward messages, and forwards from unprotected channels pass through untouched.

---

## Features

- **Multi-channel protection** — protect as many channels as you need
- **Slash commands** — configure entirely from within Discord, no SSH or file editing required
- **Persistent config** — settings survive bot restarts
- **Mod log embeds** — every blocked forward is logged with user, source, destination, and message preview
- **Admin-only commands** — requires Administrator or Manage Server permission
- **Safe by default** — ignores bots, DMs, and non-forward messages automatically
- **discord.py 2.4+ forward detection** — uses `MessageReferenceType.forward` with an integer fallback for version safety

---

## Requirements

- Python 3.10+
- discord.py 2.4+
- A Discord bot application with:
  - **Message Content Intent** enabled
  - Permissions: View Channels, Send Messages, Manage Messages, Embed Links, Read Message History
  - Scopes: `bot`, `applications.commands`

---

## Setup

**1. Clone the repo**
```bash
git clone https://github.com/michaelpentz/discord-forward-blocker.git
cd discord-forward-blocker
```

**2. Install dependencies**
```bash
# Using a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

**3. Create your config**
```bash
cp config.example.json config.json
```

Edit `config.json`:
```json
{
  "token": "YOUR_BOT_TOKEN_HERE",
  "guild_id": 123456789012345678,
  "protected_channels": [],
  "mod_log_channel": null
}
```

- `token` — your bot token from the [Discord Developer Portal](https://discord.com/developers/applications)
- `guild_id` — your server's ID (right-click server name → Copy Server ID, requires Developer Mode)
- `protected_channels` — leave empty; use `/protect` in Discord to add channels
- `mod_log_channel` — leave null; use `/setmodlog` in Discord to set it

**Lock down config permissions (important — your token is in here):**
```bash
chmod 600 config.json   # Linux/macOS
```

**4. Run the bot**
```bash
python bot.py
```

Expected output:
```
2026-03-07 12:00:00 [INFO] Starting Forward Blocker...
2026-03-07 12:00:01 [INFO] Forward Blocker ready — logged in as YourBot#0000 (ID: ...)
2026-03-07 12:00:01 [INFO] Slash commands synced to guild ...
```

---

## Slash Commands

All commands require **Administrator** or **Manage Server** permission and respond ephemerally (only visible to you).

| Command | Description |
|---|---|
| `/protect #channel` | Add a channel to the protected list |
| `/unprotect #channel` | Remove a channel from the protected list |
| `/setmodlog #channel` | Set the mod log channel for deletion embeds |
| `/status` | Show current config (protected channels + mod log) |

---

## Persistent Hosting (Linux / Raspberry Pi)

To keep the bot running after reboots, add a cron entry:

```bash
crontab -e
```

Add this line (adjust the path to your venv and script):
```
@reboot sleep 30 && /path/to/venv/bin/python /path/to/bot.py >> /path/to/bot.log 2>&1
```

---

## Project Structure

```
discord-forward-blocker/
├── bot.py                # Bot — single file, ~260 lines
├── config.json           # Your config — gitignored, never committed
├── config.example.json   # Template with placeholder values
├── requirements.txt
└── .gitignore
```

---

## Tech Stack

- **Python 3.10+**
- **discord.py 2.4+** — uses `MessageReferenceType.forward` and `message.snapshots` (added in discord.py 2.4 / Discord API 2024)
- **JSON** — simple flat config, auto-managed by slash commands
- Event-driven architecture — zero CPU usage when idle

---

## License

MIT
