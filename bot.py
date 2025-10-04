import os
import discord
from datetime import datetime
from dotenv import load_dotenv
from database import Database
import google.generativeai as genai
import asyncio


class DiscordRTFMBot:
    TRIGGER_PHRASE = ["rtfm", "RTFM", "Rtfm", "Read The F***ing Manual"]


    def __init__(self, bot_token, gemini_api_key, gemini_api_secret):
        # Load tokens and configure Gemini API
        self.BOT_TOKEN = bot_token
        self.GEMINI_API_KEY = gemini_api_key
        self.GEMINI_API_SECRET = gemini_api_secret
        genai.configure(api_key=self.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.5-flash')


        # Initialize database
        self.db = Database()


        # Discord client
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)


        # Register events
        self.client.event(self.on_ready)
        self.client.event(self.on_message)


    async def generate_response(self, question):
        """
        Generate a response using Chroma database results and Gemini API
        """
        try:
            # Query the database for relevant messages
            query_results = self.db.query(question, k=10, min_confidence=0.3, max_results=5)
           
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
            response = self.model.generate_content(prompt)
            return response.text
           
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Sorry, I encountered an error while trying to answer your question."


    async def on_ready(self):
        print(f'We have logged in as {self.client.user}')


    async def on_message(self, message):
        if message.author == self.client.user:
            return


        # Store message in database
        message_creation_time = message.created_at
        formatted_time = message_creation_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        self.db.add_message(
            content=message.content,
            username=str(message.author),
            date=formatted_time
        )
        print(f"[{formatted_time}] [{message.channel}] {message.author}: {message.content}", flush=True)
        print(f"Message stored in database: {message.content[:50]}...", flush=True)


        # Check for trigger phrase
        if any(phrase.lower() in message.content.lower() for phrase in self.TRIGGER_PHRASE):
            print(f"Trigger phrase detected in message: {message.content}", flush=True)
           
            # Remove trigger phrase to extract question
            question = message.content
            for phrase in self.TRIGGER_PHRASE:
                question = question.replace(phrase, "").strip()
           
            if question:
                print(f"Generating response for question: {question}", flush=True)
                response = await self.generate_response(question)
                if len(response)==0:
                    await message.channel.send("Please Ask A Question That Has Been Talked About Before.")
                await message.channel.send(response)
            else:
                await message.channel.send(
                    "Please ask a specific question after the trigger phrase so I can help you find relevant information from the chat history."
                )


    def run(self):
        self.client.run(self.BOT_TOKEN)




if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    BOT_TOKEN = os.getenv("DISCORD_TOKEN")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_API_SECRET = os.getenv("GEMINI_API_SECRET")


    bot = DiscordRTFMBot(BOT_TOKEN, GEMINI_API_KEY, GEMINI_API_SECRET)
    bot.run()

