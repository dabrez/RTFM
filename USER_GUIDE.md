# User Guide: RTFM Discord Bot

Never lose track of a conversation again. RTFM is an AI-powered Discord bot that remembers your chat history and answers questions based on past discussions.

---

## 🚀 How to Add the Bot to Your Server

1. **Click the Add Link**: Visit the [RTFM Dashboard](http://localhost:8080) (or the link provided by your administrator) and click the **Add to Discord** button.
2. **Select Your Server**: Choose the server where you want to add the bot. You must have "Manage Server" permissions.
3. **Authorize Permissions**: Ensure the bot has the following permissions:
   - View Channels
   - Send Messages
   - Read Message History
   - Embed Links
4. **Enable Message Content Intent**: (For server owners) Make sure the **Message Content Intent** is enabled in the Discord Developer Portal if you are hosting the bot yourself.

---

## 💬 How to Use the Bot

Once the bot is in your server, it will automatically start indexing all new messages.

### Ask a Question
To retrieve information from the chat history, use the trigger phrase `RTFM` followed by your question.

**Example Commands:**
- `RTFM what did we decide about the project deadline?`
- `RTFM who is responsible for the database setup?`
- `RTFM summarize the discussion from yesterday afternoon.`

### AI Intelligence
The bot uses **Google Gemini** to analyze retrieved messages and provide a concise, natural language response based *only* on the context it finds in your server's history.

---

## 📊 View Your History
If the dashboard is enabled, you can log in to view a history of all AI queries made in your server. This helps you track what information people are looking for.

1. Go to the [Dashboard](http://localhost:8080).
2. Click **Login with Discord**.
3. Select your server to see the log of questions and answers.

---

## 🛠️ Support
If the bot isn't responding:
- Check if it has permission to see the channel.
- Ensure you are using the `RTFM` prefix correctly.
- Contact your server administrator to ensure the bot service is running.
