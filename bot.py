#!/usr/bin/env python3
"""
Discord Forward Blocker
Deletes messages forwarded from protected channels and logs them to a mod channel.
"""

import discord
from discord import app_commands
import json
import logging
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────

CONFIG_PATH = Path(__file__).parent / "config.json"


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(config: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


# ── Bot Setup ─────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

log = logging.getLogger("forward-blocker")


# ── Embed Builder ─────────────────────────────────────────────────────────────

def build_embed(message: discord.Message) -> discord.Embed:
    """Build a red embed logging the blocked forward."""
    embed = discord.Embed(
        title="🗑️ Forward Blocked",
        color=0xe74c3c,
        timestamp=message.created_at,
    )

    # User who tried to forward
    embed.add_field(name="User", value=message.author.mention, inline=True)

    # Source channel (where the original message lived)
    source = bot.get_channel(message.reference.channel_id)
    embed.add_field(
        name="From",
        value=source.mention if source else f"<#{message.reference.channel_id}>",
        inline=True,
    )

    # Destination channel (where they tried to post the forward)
    embed.add_field(name="To", value=message.channel.mention, inline=True)

    # Content preview from message snapshot
    snapshots = getattr(message, "snapshots", [])
    if snapshots:
        snap_msg = getattr(snapshots[0], "message", None)
        if snap_msg:
            content = getattr(snap_msg, "content", "") or ""
            attachments = getattr(snap_msg, "attachments", [])
            preview = content[:100]
            if attachments:
                preview += ("  " if preview else "") + "🖼️" * min(len(attachments), 3)
            if preview.strip():
                embed.add_field(name="Message Preview", value=preview, inline=False)

    embed.set_footer(text=f"User ID: {message.author.id}")
    return embed


# ── Events ────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    config = load_config()
    guild = discord.Object(id=config["guild_id"])
    tree.copy_global_to(guild=guild)
    await tree.sync(guild=guild)
    log.info(f"Forward Blocker ready — logged in as {bot.user} (ID: {bot.user.id})")
    log.info(f"Slash commands synced to guild {config['guild_id']}")


@bot.event
async def on_message(message: discord.Message):
    # Ignore bots and DMs
    if message.author.bot:
        return
    if not message.guild:
        return

    config = load_config()

    # ── Forward detection ────────────────────────────────────────────────────
    # Forwards have a reference with type FORWARD (int value 1)
    # Regular replies have type DEFAULT (int value 0)
    ref = message.reference
    if ref is None:
        return

    # Handle both enum and raw int (discord.py version safety)
    ref_type = getattr(ref, "type", None)
    forward_type = getattr(discord, "MessageReferenceType", None)
    is_forward = (
        (forward_type is not None and ref_type == forward_type.forward)
        or (isinstance(ref_type, int) and ref_type == 1)
    )

    if not is_forward:
        return

    if ref.channel_id not in config.get("protected_channels", []):
        return

    # ── Delete the forward ───────────────────────────────────────────────────
    try:
        await message.delete()
        log.info(
            f"Deleted forward by {message.author} ({message.author.id}) "
            f"from channel {ref.channel_id} into #{message.channel.name}"
        )
    except discord.Forbidden:
        log.error(f"Missing Manage Messages permission in #{message.channel.name}")
        return
    except discord.NotFound:
        log.warning("Message already deleted before bot could act")
        return

    # ── Post to mod log ──────────────────────────────────────────────────────
    mod_log_id = config.get("mod_log_channel")
    if not mod_log_id:
        log.warning("mod_log_channel not configured — skipping embed (use /setmodlog)")
        return

    mod_channel = bot.get_channel(mod_log_id)
    if not mod_channel:
        log.warning(f"Could not find mod log channel ID {mod_log_id}")
        return

    try:
        await mod_channel.send(embed=build_embed(message))
    except discord.Forbidden:
        log.error(f"Missing Send Messages permission in mod log channel {mod_log_id}")


# ── Permission Guard ──────────────────────────────────────────────────────────

def admin_only():
    """Restrict command to Administrator or Manage Server permissions."""
    async def predicate(interaction: discord.Interaction) -> bool:
        perms = interaction.user.guild_permissions
        return perms.administrator or perms.manage_guild
    return app_commands.check(predicate)


# ── /protect ──────────────────────────────────────────────────────────────────

@tree.command(name="protect", description="Protect a channel — forwards from it will be deleted")
@app_commands.describe(channel="Channel to protect")
@admin_only()
async def cmd_protect(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_config()
    if channel.id in config["protected_channels"]:
        await interaction.response.send_message(
            f"{channel.mention} is already protected.", ephemeral=True
        )
        return
    config["protected_channels"].append(channel.id)
    save_config(config)
    log.info(f"{interaction.user} added #{channel.name} to protected channels")
    await interaction.response.send_message(
        f"✅ {channel.mention} is now protected — forwards from it will be deleted.",
        ephemeral=True,
    )


# ── /unprotect ────────────────────────────────────────────────────────────────

@tree.command(name="unprotect", description="Remove a channel from the protected list")
@app_commands.describe(channel="Channel to unprotect")
@admin_only()
async def cmd_unprotect(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_config()
    if channel.id not in config["protected_channels"]:
        await interaction.response.send_message(
            f"{channel.mention} is not in the protected list.", ephemeral=True
        )
        return
    config["protected_channels"].remove(channel.id)
    save_config(config)
    log.info(f"{interaction.user} removed #{channel.name} from protected channels")
    await interaction.response.send_message(
        f"✅ {channel.mention} removed from the protected list.", ephemeral=True
    )


# ── /setmodlog ────────────────────────────────────────────────────────────────

@tree.command(name="setmodlog", description="Set the channel where the bot logs deleted forwards")
@app_commands.describe(channel="Mod log channel")
@admin_only()
async def cmd_setmodlog(interaction: discord.Interaction, channel: discord.TextChannel):
    config = load_config()
    config["mod_log_channel"] = channel.id
    save_config(config)
    log.info(f"{interaction.user} set mod log to #{channel.name}")
    await interaction.response.send_message(
        f"✅ Mod log set to {channel.mention}.", ephemeral=True
    )


# ── /status ───────────────────────────────────────────────────────────────────

@tree.command(name="status", description="Show the bot's current configuration")
@admin_only()
async def cmd_status(interaction: discord.Interaction):
    config = load_config()

    protected = config.get("protected_channels", [])
    mod_log = config.get("mod_log_channel")

    protected_str = "\n".join(f"<#{cid}>" for cid in protected) or "None set"
    mod_log_str = f"<#{mod_log}>" if mod_log else "Not set — use `/setmodlog`"

    embed = discord.Embed(title="🗑️ Forward Blocker — Status", color=0x2ecc71)
    embed.add_field(name="Protected Channels", value=protected_str, inline=False)
    embed.add_field(name="Mod Log Channel", value=mod_log_str, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler()],
    )

    config = load_config()

    if not config.get("token"):
        log.error("No token found in config.json — add your bot token and restart")
        raise SystemExit(1)

    if not config.get("guild_id"):
        log.error("No guild_id found in config.json — add your server ID and restart")
        raise SystemExit(1)

    log.info("Starting Forward Blocker...")
    bot.run(config["token"], log_handler=None)
