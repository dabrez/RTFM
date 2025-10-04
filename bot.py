import os
import discord
from datetime import datetime
from dotenv import load_dotenv
from database import Database
import google.generativeai as genai

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_SECRET = os.getenv("GEMINI_API_SECRET")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

TRIGGER_PHRASE = ["rtfm", "RTFM", "Rtfm", "Read The F***ing Manual"]

# Initialize database
db = Database()

async def generate_response(question):
    """
    Generate a response using Chroma database results and Gemini API
    """
    try:
        # Query the database for relevant messages
        query_results = db.query(question, k=10, min_confidence=0.3, max_results=5)
        
        if not query_results:
            return "I couldn't find any relevant information in the chat history to answer your question."
        
        # Prepare context from database results
        context = ""
        for content, metadata, confidence in query_results:
            context += f"[{metadata['date']}] {metadata['username']}: {content}\n"
        
        # Create prompt for Gemini
        prompt = f"""Based on the following Discord chat history, please answer the question: "{question}"

Chat History:
{context}

Please provide a helpful and accurate response based on the information available in the chat history. If the information is insufficient, say so clearly."""
        
        # Generate response using Gemini
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Sorry, I encountered an error while trying to answer your question."

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
    
    # Store message in ChromaDB for vectorization
    db.add_message(
        content=message.content,
        username=str(message.author),
        date=formatted_time
    )
    print(f"Message stored in database: {message.content[:50]}...", flush=True)

    if any(phrase.lower() in message.content.lower() for phrase in TRIGGER_PHRASE):
        print(f"Trigger phrase detected in message: {message.content}", flush=True)
        
        # Extract the question from the message (remove trigger phrase)
        question = message.content
        for phrase in TRIGGER_PHRASE:
            question = question.replace(phrase, "").strip()
        
        if question:
            print(f"Generating response for question: {question}", flush=True)
            response = await generate_response(question)
            await message.channel.send(response)
        else:
            await message.channel.send("Please ask a specific question after the trigger phrase so I can help you find relevant information from the chat history.")

client.run(BOT_TOKEN)
