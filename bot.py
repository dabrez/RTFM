import os
import discord
from datetime import datetime
from dotenv import load_dotenv
import asyncio
import uuid
import logging
import time
from typing import Optional
import google.generativeai as genai

from database import Database, PostgresDatabase, CacheManager
from utils import CircuitBreaker

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DiscordRTFMBot:
    TRIGGER_PHRASE = ["rtfm", "RTFM", "Rtfm", "Read The F***ing Manual"]

    def __init__(self, bot_token, gemini_api_key=None):
        # Load tokens
        self.BOT_TOKEN = bot_token

        # Initialize databases
        self.db = Database()
        self.postgres = PostgresDatabase()
        self.cache = CacheManager()
        
        # Initialize Gemini
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.circuit_breaker = CircuitBreaker("GeminiAPI")
        else:
            self.model = None
            logger.warning("No Gemini API key provided - AI responses disabled")

        # Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)

        # Register events
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

    async def on_ready(self):
        logger.info(f'Logged in as {self.client.user}')

    async def on_message(self, message):
        if message.author == self.client.user:
            return

        # 1. Store message in ChromaDB asynchronously
        asyncio.create_task(self._store_message(message))

        # 2. Check for trigger phrase
        if any(phrase.lower() in message.content.lower() for phrase in self.TRIGGER_PHRASE):
            logger.info(f"Trigger phrase detected in message: {message.content}")

            # Remove trigger phrase to extract question
            question = message.content
            for phrase in self.TRIGGER_PHRASE:
                question = question.replace(phrase, "").strip()

            if question:
                # Start typing indicator
                async with message.channel.typing():
                    # Process query and get response
                    response_text = await self._process_query(message, question)
                    await message.channel.send(response_text)
            else:
                await message.channel.send(
                    "Please ask a specific question after the trigger phrase so I can help you find relevant information from the chat history."
                )

    async def _store_message(self, message):
        """Store message in ChromaDB"""
        try:
            # message.created_at is naive UTC in discord.py if not specified
            timestamp = message.created_at.isoformat()
            
            # Use the local ChromaDB via Database class
            self.db.add_message(
                content=message.content,
                username=str(message.author),
                guild_id=str(message.guild.id) if message.guild else "DM",
                date=timestamp
            )
            logger.debug(f"Stored message {message.id} from {message.author}")
        except Exception as e:
            logger.error(f"Error storing message: {e}")

    async def _process_query(self, message, question: str) -> str:
        """Handle query logic: Cache -> ChromaDB -> Gemini"""
        try:
            guild_id = str(message.guild.id) if message.guild else "DM"
            
            # 1. Check Redis cache
            cached_response = self.cache.get_response(question)
            if cached_response:
                logger.info("Found response in cache")
                return f"[Cached] {cached_response}"

            # 2. Query ChromaDB for context
            if not self.model:
                return "AI responses are currently disabled (no API key configured)."

            query_results = self.db.query(
                question,
                guild_id=guild_id,
                k=10,
                min_confidence=0.3,
                max_results=5
            )

            if not query_results:
                return "I couldn't find any relevant information in the chat history to answer your question."

            # Prepare context
            context = ""
            for content, metadata, confidence in query_results:
                context += f"[{metadata['date']}] {metadata['username']}: {content}\n"

            # 3. Generate response with Gemini
            prompt = f"""Based on the following Discord chat history, please answer the question: "{question}"

Chat History:
{context}

Please provide a helpful and accurate response based on the information available in the chat history. If the information is insufficient, say so clearly."""

            # Use CircuitBreaker for API call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.circuit_breaker.call(self.model.generate_content, prompt)
            )
            
            response_text = response.text

            # 4. Store in Cache
            self.cache.set_response(question, response_text)

            # 5. Log to Postgres
            query_id = str(uuid.uuid4())
            self.postgres.log_query(
                query_id=query_id,
                question=question,
                response=response_text,
                username=str(message.author),
                user_id=str(message.author.id),
                guild_id=guild_id,
                channel_id=str(message.channel.id)
            )

            return response_text

        except Exception as e:
            logger.error(f"Error processing query: {e}", exc_info=True)
            return f"Sorry, I encountered an error: {str(e)}"

    def run(self):
        try:
            self.client.run(self.BOT_TOKEN)
        except Exception as e:
            logger.error(f"Bot failed to start: {e}")


if __name__ == "__main__":
    load_dotenv()
    BOT_TOKEN = os.getenv("DISCORD_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    if not BOT_TOKEN:
        logger.error("DISCORD_TOKEN not found in environment variables")
        exit(1)

    bot = DiscordRTFMBot(BOT_TOKEN, GEMINI_API_KEY)
    bot.run()
