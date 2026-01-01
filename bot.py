import discord
from discord.ext import commands
import json
import os
from aiohttp import web

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

# -------------------------
# GAMEMODES
# -------------------------
GAMEMODES = [
    "sword",
    "axe_shield",
    "mace",
    "nethpot",
    "diasmp",
    "nethsmp",
    "uhc",
    "crystal",
    "cartpvp",
    "diapot"
]

# -------------------------
# TIERS
# -------------------------
TIERS = {
    "default": [
        "HT1", "LT1",
        "HT2", "LT2",
        "HT3", "LT3",
        "HT4", "LT4",
        "HT5", "LT5"
    ]
}

# -------------------------
# DATA HELPERS
# -------------------------
def load():
    if not os.path.exists(DATA_FILE):
        return {"tiers": {}, "log_channel_id": None}
    with open(DATA_FILE) as f:
        return json.load(f)


def save(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)


data = load()


def ensure_gamemode(gamemode):
    gamemode = gamemode.lower()

    if gamemode not in GAMEMODES:
        return None

    if gamemode not in data["tiers"]:
        data["tiers"][gamemode] = {}
        save(data)

    return gamemode


def get_tier_list(gamemode):
    if gamemode in TIERS:
        return TIERS[gamemode]
    return TIERS["default"]


async def log_change(guild, embed: discord.Embed):
    channel_id = data.get("log_channel_id")
    if not channel_id:
        return

    channel = guild.get_channel(channel_id)
    if channel:
        await channel.send(embed=embed)


# -------------------------
# COMMANDS
# -------------------------

@bot.command()
@commands.has_permissions(manage_guild=True)
async def setlogchannel(ctx):
    """
    Set the channel where tier changes are logged.
    Run inside the channel you want.
    """
    data["log_channel_id"] = ctx.channel.id
    save(data)

    embed = discord.Embed(
        title="📡 Log Channel Set",
        description=f"Tier changes will be logged here.",
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)


@bot.command()
@commands.has_permissions(manage_guild=True)
async def settier(ctx, member: discord.Member, gamemode: str, tier: str):
    gamemode = ensure_gamemode(gamemode)

    if gamemode is None:
        await ctx.send("❌ Invalid gamemode. Use `!modes`.")
        return

    tier_list = get_tier_list(gamemode)
    tier = tier.upper()

    if tier not in tier_list:
        await ctx.send(
            f"❌ Invalid tier.\nAvailable: `{', '.join(tier_list)}`"
        )
        return

    data["tiers"][gamemode][str(member.id)] = tier
    save(data)

    embed = discord.Embed(
        title="Tier Updated ✅",
        description=f"**{member.display_name}** is now **{tier}** in **{gamemode}**",
        color=discord.Color.green(),
    )
    await ctx.send(embed=embed)

    log_embed = discord.Embed(
        title="📝 Tier Change Logged",
        description=(
            f"👤 **{member.display_name}**\n"
            f"🎮 Gamemode: **{gamemode}**\n"
            f"🏷 New Tier: **{tier}**\n"
            f"🔧 Changed by: {ctx.author.mention}"
        ),
        color=discord.Color.blue()
    )

    await log_change(ctx.guild, log_embed)


@bot.command()
async def tier(ctx, member: discord.Member, gamemode: str):
    gamemode = ensure_gamemode(gamemode)

    if gamemode is None:
        await ctx.send("❌ Invalid gamemode. Use `!modes`.")
        return

    user_id = str(member.id)
    tier = data["tiers"][gamemode].get(user_id, "No Tier")

    embed = discord.Embed(
        title=f"{gamemode.upper()} — Player Tier",
        description=f"**{member.display_name}** → **{tier}**",
        color=discord.Color.blurple()
    )

    await ctx.send(embed=embed)


@bot.command()
async def tierlb(ctx, gamemode: str):
    gamemode = ensure_gamemode(gamemode)

    if gamemode is None:
        await ctx.send("❌ Invalid gamemode. Use `!modes`.")
        return

    tier_list = get_tier_list(gamemode)

    leaderboard = sorted(
        data["tiers"][gamemode].items(),
        key=lambda x: tier_list.index(x[1])
    )

    if not leaderboard:
        await ctx.send(f"No players ranked in **{gamemode}** yet.")
        return

    embed = discord.Embed(
        title=f"🏆 Leaderboard — {gamemode.upper()}",
        color=discord.Color.purple()
    )

    lines = []
    for uid, tier in leaderboard:
        member = ctx.guild.get_member(int(uid))
        name = member.display_name if member else "Unknown"
        lines.append(f"**{name}** — {tier}")

    embed.description = "\n".join(lines)

    await ctx.send(embed=embed)


@bot.command()
async def modes(ctx):
    embed = discord.Embed(
        title="🎮 Available Gamemodes",
        description="\n".join([f"- {m}" for m in GAMEMODES]),
        color=discord.Color.orange()
    )

    await ctx.send(embed=embed)


import asyncio
from aiohttp import web
import os

async def run_bot():
    await bot.start(os.getenv("BOT_TOKEN"))

async def handle(request):
    return web.Response(text="Bot is running")

async def run_web():
    app = web.Application()
    app.add_routes([web.get("/", handle)])
    port = int(os.getenv("PORT", 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

async def main():
    await asyncio.gather(run_bot(), run_web())

asyncio.run(main())
