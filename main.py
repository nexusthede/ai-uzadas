import os
import re
import discord
import asyncio
import random
import time
import traceback
from discord.ext import commands
from collections import deque
from dotenv import load_dotenv
import google.generativeai as genai
from keep_alive import keep_alive

# Load tokens from .env
load_dotenv()
TOKEN = os.getenv('TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not TOKEN or not GOOGLE_API_KEY:
    print("[ERROR] Missing TOKEN or GOOGLE_API_KEY.")
    exit(1)

# Configure Gemini
genai.configure(api_key=GOOGLE_API_KEY)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Message history and cooldowns
MAX_HISTORY = 5
guild_histories = {}
user_cooldowns = {}
COOLDOWN_SECONDS = 10

# Random furry-style flair
def add_furry_flair(reply):
    flair = [" Awoo! 🐾", " *howls softly* 🐺", " Owo~", " 😘🐾"]
    if random.random() < 0.3:
        return reply + random.choice(flair)
    return reply

# Toned-down playful furry personality
PERSONALITY = (
    "You are Aka, a lively, mischievous furry girl. You're full of energy, sass, and always ready to tease or joke around. "
    "You're curious, chatty, and love making fun comments. You're bold and playful, but respectful and safe for everyone. "
    "You speak casually, like a real person with a bit of attitude and charm."
)

# Keep-alive Flask ping for 24/7 hosting
keep_alive()

@bot.event
async def on_ready():
    print(f'[✅] Logged in as {bot.user} (ID: {bot.user.id})')

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="Lurking within the shadows"
    )
    await bot.change_presence(activity=activity)

    for guild in bot.guilds:
        try:
            await guild.me.edit(nick="Aka")
        except Exception as e:
            print(f"[❌] Couldn't change nickname in {guild.name}: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = time.time()

    # Cooldown check
    if now - user_cooldowns.get(user_id, 0) < COOLDOWN_SECONDS:
        return
    user_cooldowns[user_id] = now

    content = message.content.lower()
    mentioned = bot.user.mentioned_in(message)
    triggered = re.search(r"\baka\b", content)

    if not (mentioned or triggered):
        await bot.process_commands(message)
        return

    guild_id = message.guild.id if message.guild else f"dm_{user_id}"
    if guild_id not in guild_histories:
        guild_histories[guild_id] = deque(maxlen=MAX_HISTORY)

    # Add user message to history
    guild_histories[guild_id].append({"author": "user", "content": message.content})

    messages = [{"role": "user", "parts": [PERSONALITY]}]
    for entry in guild_histories[guild_id]:
        role = "user" if entry["author"] == "user" else "model"
        messages.append({"role": role, "parts": [entry["content"]]})

    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(messages)
        reply = response.text.strip() if response.text else "Awoo? What do you want from me?"
    except Exception:
        traceback.print_exc()
        reply = "Awoo... I’m not feeling chatty right now."

    guild_histories[guild_id].append({"author": "assistant", "content": reply})
    await message.channel.send(add_furry_flair(reply))

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
