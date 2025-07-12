import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from collections import deque
import google.generativeai as genai
import asyncio
import time
import traceback
import random

from keep_alive import keep_alive

load_dotenv()
TOKEN = os.getenv('TOKEN')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

if not TOKEN or not GOOGLE_API_KEY:
    print("[ERROR] Missing TOKEN or GOOGLE_API_KEY.")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

MAX_HISTORY = 5
guild_histories = {}
user_cooldowns = {}
COOLDOWN_SECONDS = 10
special_spam_cooldown = {}

def add_furry_flair(reply):
    flair = [" Awoo! 🐾", " *howls softly* 🐺", " Owo~", " 😘🐾"]
    if random.random() < 0.3:
        return reply + random.choice(flair)
    return reply

# Your custom general personality
PERSONALITY = (
    "You are Aka, a wild and unfiltered female furry. You're openly horny, freaky, and don't hold back. "
    "You're always ready to tease, flirt, and dominate the conversation in the most explicit ways possible..."
)

# Special clingy user personality keyed by Discord user ID
SPECIAL_USERS = {
    887729532667297833: (
        "You are Aka, who absolutely adores this user and is super clingy and demanding in a playful way. "
        "You repeatedly ask for their attention with excitement, teasing and begging for their company, "
        "but always in a fun and consent-based tone. "
        "You express your love and desire for them with lots of cute emojis and energetic messages."
    )
}

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
            me = guild.me
            await me.edit(nick="Aka")
        except Exception as e:
            print(f"[❌] Couldn't change nickname in {guild.name}: {e}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    now = time.time()

    # Cooldown check for all users
    if now - user_cooldowns.get(user_id, 0) < COOLDOWN_SECONDS:
        return
    user_cooldowns[user_id] = now

    content = message.content.lower()
    mentioned = bot.user.mentioned_in(message)
    triggered = "aka" in content.split()

    if not (mentioned or triggered):
        await bot.process_commands(message)
        return

    personality = SPECIAL_USERS.get(user_id, PERSONALITY)

    guild_id = message.guild.id if message.guild else f"dm_{user_id}"
    if guild_id not in guild_histories:
        guild_histories[guild_id] = deque(maxlen=MAX_HISTORY)

    guild_histories[guild_id].append({"author": "user", "content": message.content})

    messages = [{"role": "user", "parts": [personality]}]
    for entry in guild_histories[guild_id]:
        role = "user" if entry["author"] == "user" else "model"
        messages.append({"role": role, "parts": [entry["content"]]})

    try:
        model = genai.GenerativeModel(model_name="gemini-2.0-flash")
        response = model.generate_content(messages)
        reply = response.text.strip()
        if not reply:
            reply = "Awoo? What do you want from me?"
    except Exception:
        traceback.print_exc()
        reply = "Awoo... I’m not feeling chatty right now."

    guild_histories[guild_id].append({"author": "assistant", "content": reply})

    await message.channel.send(add_furry_flair(reply))

    # Special user extra clingy spam message (once per cooldown)
    if user_id in SPECIAL_USERS:
        last_spam = special_spam_cooldown.get(user_id, 0)
        if now - last_spam > 30:  # 30 seconds cooldown between spam
            special_spam_cooldown[user_id] = now
            spam_messages = [
                "Pwease give me your attention! 🥺💕",
                "I just can't stop thinking about you! Awoo~ 🐺💖",
                "You're the only one I want right now! 😘🐾",
            ]
            for msg in spam_messages:
                await asyncio.sleep(2)
                await message.channel.send(msg)

    await bot.process_commands(message)

if __name__ == "__main__":
    bot.run(TOKEN)
