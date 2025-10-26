# RTFM Discord Bot

AI-powered Discord Chat Memory Bot that tracks and embeds all server messages into a Chroma vector database using HuggingFace sentence embeddings. When prompted (e.g., "RTFM when is the meeting?"), it performs a similarity search to retrieve contextually relevant chat messages and generates a response using Google Gemini.

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Docker & Docker Compose installed
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- Google Gemini API Key ([Get one here](https://makersuite.google.com/app/apikey))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/rtfm-discord-bot.git
cd rtfm-discord-bot

# 2. Initialize (creates .env file)
make setup

# 3. Edit .env with your tokens
nano .env

# 4. Build and start the bot
make init

# 5. View logs
make logs
```

That's it! Your bot is now running and storing messages.

## 📋 Current Structure (Simple - MVP)

```
rtfm-discord-bot/
├── bot.py                  # Main Discord bot logic
├── database.py             # ChromaDB vector database interface
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker container definition
├── docker-compose.yml     # Docker orchestration
├── .env.example           # Environment template
├── .gitignore            # Git ignore rules
├── Makefile              # Convenient commands
└── discord_db/           # ChromaDB storage (auto-created)
```

## 🎯 How It Works

1. **Message Capture**: Bot listens to all Discord messages
2. **Embedding**: Each message is converted to a vector embedding using `sentence-transformers/all-MiniLM-L6-v2`
3. **Storage**: Embeddings stored in ChromaDB with metadata (username, timestamp)
4. **Query**: When user types "RTFM [question]", bot:
   - Converts question to embedding
   - Performs similarity search in ChromaDB
   - Retrieves top relevant messages
   - Sends context to Google Gemini
   - Returns AI-generated response

## 💬 Usage

Simply type in any Discord channel where the bot is present:

```
RTFM when is the meeting tomorrow?
RTFM what did John say about the project?
RTFM who is working on the frontend?
```

The bot will search through all past messages and generate a contextual response.

## 🛠️ Available Commands

```bash
make help          # Show all commands
make setup         # Initial setup
make build         # Build Docker image
make up            # Start bot
make down          # Stop bot
make restart       # Restart bot
make logs          # View live logs
make logs-tail     # View last 100 lines
make status        # Check bot status
make shell         # Open shell in container
make rebuild       # Rebuild and restart
make clean         # Remove containers
make clean-all     # Remove everything (including database!)
make init          # Complete initialization
```

## 📦 Dependencies

- **discord.py** - Discord API wrapper
- **chromadb** - Vector database
- **sentence-transformers** - Text embeddings
- **google-generativeai** - Gemini API
- **langchain-community** - Vector store utilities

## 🔧 Configuration

Edit `.env` file:

```bash
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_gemini_api_key
GEMINI_API_SECRET=your_gemini_secret
```

## 📊 Future Architecture (Scalable - 6 Week Refactor)

The current simple structure is the **MVP**. The plan is to refactor into a **scalable microservices architecture**:

### Target Architecture

```
rtfm-discord-bot/
├── src/
│   ├── bot/                    # Discord bot service
│   ├── kafka/                  # Event streaming (senior dev)
│   ├── rag/                    # RAG pipeline (Dev 4)
│   ├── database/               # PostgreSQL (Dev 2)
│   ├── cache/                  # Redis caching
│   ├── workers/                # Background workers
│   │   ├── embedding_worker.py
│   │   └── indexing_worker.py
│   ├── monitoring/             # Prometheus metrics (Dev 5)
│   └── api/                    # FastAPI (optional)
├── docker/
│   ├── Dockerfile.bot
│   ├── Dockerfile.worker
│   └── Dockerfile.api
├── monitoring/
│   ├── prometheus/
│   └── grafana/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/
```

### Planned Services (Future)

1. **Zookeeper** - Kafka coordination
2. **Kafka** - Event streaming for messages
3. **PostgreSQL** - Metadata & guild configs
4. **Redis** - Caching layer
5. **ChromaDB** - Vector embeddings (keep current)
6. **Embedding Workers** - Async embedding generation (scalable)
7. **Indexing Workers** - Vector indexing (scalable)
8. **Prometheus** - Metrics collection
9. **Grafana** - Dashboards & monitoring
10. **FastAPI** (optional) - Admin web interface

### Refactoring Timeline (6 Weeks)

**Week 1-2**: Infrastructure
- Set up Kafka (Senior Dev)
- Add PostgreSQL for metadata (Dev 2)
- Docker orchestration improvements (Dev 1)

**Week 3**: Separation of Concerns
- Split bot logic into microservices
- Add Redis caching (Dev 2)
- Background workers for embeddings

**Week 4**: Monitoring & Observability
- Prometheus metrics (Dev 5)
- Grafana dashboards
- Logging improvements

**Week 5**: Advanced Features
- Multi-guild support
- Admin commands
- RAG improvements (Dev 4)

**Week 6**: Testing & Production
- Load testing
- Performance optimization
- Production deployment

### Why Refactor?

**Current (Simple)**:
- ✅ Easy to understand
- ✅ Quick to deploy
- ✅ Works for single server
- ❌ Not scalable to multiple servers
- ❌ No caching
- ❌ Limited monitoring

**Future (Microservices)**:
- ✅ Scales to 100+ Discord servers
- ✅ Redis caching reduces costs
- ✅ Background workers handle load
- ✅ Full observability
- ✅ Production-ready
- ❌ More complex
- ❌ More services to manage

## 📚 Documentation

- **REPOSITORY_STRUCTURE.md** - Complete future architecture guide
- **DOCKER_SETUP.md** - Comprehensive Docker documentation
- **docker-compose.full.yml** - Full microservices compose file (future)

## 🐛 Troubleshooting

**Bot won't connect?**
```bash
make logs  # Check for "We have logged in as" message
```

**Database issues?**
```bash
# Reset database (WARNING: deletes all data)
make clean-all
make init
```

**Docker issues?**
```bash
# Complete rebuild
make down
docker system prune -f
make build
make up
```

## 🔒 Security

- Never commit `.env` file (already in `.gitignore`)
- Keep your Discord token private
- Rotate API keys regularly
- Use strong passwords for future PostgreSQL/Redis

## 🤝 Contributing

This is a student project for CruzHacks. Current structure is intentionally simple for the MVP. Future refactoring will follow the architecture in `REPOSITORY_STRUCTURE.md`.

### Development Workflow

```bash
# Make changes to bot.py or database.py
make rebuild  # Rebuild and restart
make logs     # Check logs
```

## 📝 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- Built for CruzHacks hackathon
- Uses HuggingFace embeddings
- Powered by Google Gemini
- Inspired by "Read The F***ing Manual" culture

---

**Current Status**: ✅ MVP Complete  
**Next Phase**: 🚧 Microservices Refactor (6 weeks)  
**Team Size**: 6 developers (1 senior, 5 freshmen)
