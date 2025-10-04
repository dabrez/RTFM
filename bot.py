import os
import discord
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_SECRET = os.getenv("GEMINI_API_SECRET")

TRIGGER_PHRASE = ["rtfm", "RTFM", "Rtfm", "Read The F***ing Manual"]

# Discord Message Scraping
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    message_creation_time = message.created_at
    formatted_time = message_creation_time.strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{formatted_time}] [{message.channel}] {message.author}: {message.content}", flush=True)

    if any(phrase.lower() in message.content.lower() for phrase in TRIGGER_PHRASE):
        print(f"Trigger phrase detected in message: {message.content}", flush=True)
        await message.channel.send("Please refer to the documentation or manual for assistance.")

client.run(BOT_TOKEN)
