# message-policy-enforcer

Event-driven message policy enforcement engine that intercepts, evaluates, and acts on messages in real time based on configurable channel protection rules. Deployed on Discord as the initial enforcement target.

## Overview

Organizations need to control how content flows between communication channels. This service monitors message events, detects policy violations (such as unauthorized forwarding from protected channels), and enforces rules automatically with full audit logging.

## How It Works

1. **Event Interception**: Monitors all message creation events in real time
2. **Policy Evaluation**: Checks message metadata against configured protection rules (source channel, message type, forwarding origin)
3. **Enforcement**: Silently removes policy-violating messages
4. **Audit Logging**: Posts structured log entries to a designated audit channel with user, source, destination, and content preview

Non-violating messages pass through with zero processing overhead.

## Features

- **Configurable channel protection**: Protect any number of source channels via runtime commands
- **Runtime configuration**: All settings managed through slash commands (no SSH or file editing required)
- **Persistent state**: Configuration survives service restarts (JSON-backed)
- **Structured audit logs**: Every enforcement action logged with full context
- **Permission-gated commands**: Administrative operations require elevated permissions
- **Safe defaults**: Ignores bot messages, DMs, and non-forward events automatically

## Technical Details

| Component | Detail |
|-----------|--------|
| Language | Python 3.10+ |
| Framework | discord.py 2.4+ (MessageReferenceType.forward with integer fallback) |
| Architecture | Event-driven, async. Zero CPU when idle. |
| Configuration | JSON file, managed via slash commands at runtime |
| Deployment | Single-file service (~260 lines), suitable for systemd or container deployment |

## Commands

| Command | Description |
|---------|-------------|
| `/protect #channel` | Add a channel to the protection list |
| `/unprotect #channel` | Remove a channel from the protection list |
| `/setmodlog #channel` | Designate the audit log channel |
| `/status` | Display current policy configuration |

All commands require Administrator or Manage Server permissions and respond ephemerally.

## Setup

```bash
git clone https://github.com/michaelpentz/message-policy-enforcer.git
cd message-policy-enforcer
pip install -r requirements.txt
cp config.example.json config.json
# Add credentials to config.json
python bot.py
```

Configure channels via slash commands in the target server after the bot connects.

## License

MIT License. Copyright (c) 2026 Michael Pentz.
