import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import re

# ✅ ADDED: imports for keepalive + asyncio
import asyncio
from aiohttp import web

# -------------------- YOUR ORIGINAL SETUP --------------------
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='s!', intents=intents)

# -------------------- CONFIG --------------------
WELCOME_CHANNEL_ID = 1398947096794628206
SECRET_ROLE_NAME = "Gamer"

# ✅ Use the ROLE IDs here (right-click role → Copy ID)
AUTO_ROLE_1_ID = 1392579956269256802  # 🔧 replace with your first role ID
AUTO_ROLE_2_ID = 1392579956269256797  # 🔧 replace with your second role ID

# Emojis and link
COUNTER_EMOJI_SPEC = "<:peoples12:1416376261290491904>"
LINK_EMOJI_SPEC = "<:exam:1416376255745626273>"
LINK_LABEL = "Information"
LINK_URL = "https://discord.com/channels/1392579956143554580/1392584900674191512"

COUNT_HUMANS_ONLY = True  # True = exclude bots

# -------------------- EMOJI RESOLVER --------------------
EMOJI_REGEX = re.compile(r"<(a?):([A-Za-z0-9_~]+):(\d+)>")

def resolve_emoji(spec):
    """Converts ID / string / mention into a usable emoji for buttons."""
    if spec is None:
        return None

    # If mention string like <:name:id> or <a:name:id>
    if isinstance(spec, str):
        match = EMOJI_REGEX.fullmatch(spec.strip())
        if match:
            animated = bool(match.group(1))
            name = match.group(2)
            eid = int(match.group(3))
            return discord.PartialEmoji(name=name, id=eid, animated=animated)
        return spec  # assume Unicode emoji like "👥"

    # If raw ID number
    if isinstance(spec, int):
        emoji = bot.get_emoji(spec)
        return emoji or discord.PartialEmoji(id=spec)

    return None

# -------------------- VIEW CREATION --------------------
def make_welcome_view(guild: discord.Guild) -> discord.ui.View:
    """Create welcome view with member count + link button."""
    count = sum(1 for m in guild.members if not m.bot) if COUNT_HUMANS_ONLY else guild.member_count
    view = discord.ui.View(timeout=None)

    view.add_item(
        discord.ui.Button(
            label=f" {count}",
            style=discord.ButtonStyle.gray,
            disabled=True,
            emoji=resolve_emoji(COUNTER_EMOJI_SPEC)
        )
    )

    view.add_item(
        discord.ui.Button(
            label=LINK_LABEL,
            style=discord.ButtonStyle.link,
            url=LINK_URL,
            emoji=resolve_emoji(LINK_EMOJI_SPEC)
        )
    )

    return view

# -------------------- EVENTS --------------------
@bot.event
async def on_ready():
    print(f"We are ready to go in, {bot.user.name}")

@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild
    channel = guild.get_channel(WELCOME_CHANNEL_ID)

    if channel is None:
        print("⚠️ Channel not found. Check the channel ID.")
        return

    # Assign roles by ID
    role1 = guild.get_role(AUTO_ROLE_1_ID)
    role2 = guild.get_role(AUTO_ROLE_2_ID)

    for role in [role1, role2]:
        if role:
            try:
                await member.add_roles(role)
            except Exception as e:
                print(f"⚠️ Could not assign role {role.name}: {e}")

    view = make_welcome_view(guild)
    await channel.send(
        f"Hello {member.mention}, "
        f"welcome to **<:sflrplogo:1414185736801882133> South Florida Roleplay**! We’re glad to have you here!",
        view=view
    )

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "sflrp sucks" in message.content.lower():
        await message.delete()
        await message.channel.send(f"{message.author.mention} - don't use naughty language!")

    await bot.process_commands(message)

# -------------------- COMMANDS --------------------
@bot.command()
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
async def assign(ctx):
    role = discord.utils.get(ctx.guild.roles, name=SECRET_ROLE_NAME)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now assigned to {SECRET_ROLE_NAME}")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def remove(ctx):
    role = discord.utils.get(ctx.guild.roles, name=SECRET_ROLE_NAME)
    if role:
        await ctx.author.remove_roles(role)
        await ctx.send(f"{ctx.author.mention} has had the {SECRET_ROLE_NAME} removed")
    else:
        await ctx.send("Role doesn't exist")

@bot.command()
async def dm(ctx, *, msg):
    await ctx.author.send(f"You said {msg}")

@bot.command()
async def reply(ctx):
    await ctx.reply("This is a reply to your message!")

@bot.command()
async def poll(ctx, *, question):
    embed = discord.Embed(title="New Poll", description=question)
    poll_message = await ctx.send(embed=embed)
    await poll_message.add_reaction("👍")
    await poll_message.add_reaction("👎")

# -------------------- KEEPALIVE (ADDED) --------------------
# Tiny HTTP server so UptimeRobot/Render can ping "/"
async def _keepalive_handle(request):
    return web.Response(text="OK")

async def _run_keepalive(port: int):
    app = web.Application()
    app.router.add_get("/", _keepalive_handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()

# -------------------- RUN (REPLACED) --------------------
# Render sets PORT; default to 10000 for local runs
PORT = int(os.getenv("PORT", "10000"))

async def _main():
    # start the keepalive HTTP server in the background
    asyncio.create_task(_run_keepalive(PORT))
    # start the bot (replaces bot.run)
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(_main())
