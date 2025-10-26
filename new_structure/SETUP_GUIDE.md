# RTFM Discord Bot - Setup Guide

## 🎯 Overview

This is the **current simple structure** (MVP version). It's intentionally simple with just 2 Python files and Docker setup. The full microservices architecture is planned for the 6-week refactoring phase.

## 📦 What You Have

### Current Files (Simple Structure)
```
rtfm-discord-bot/
├── bot.py                 # Main bot logic (you already have this)
├── database.py            # Vector database (you already have this)
├── Dockerfile             # Docker container setup (NEW)
├── docker-compose.yml     # Docker orchestration (NEW)
├── requirements.txt       # Python dependencies (NEW)
├── .env.example          # Environment template (NEW)
├── .gitignore            # Git ignore rules (you already have this)
├── Makefile              # Convenient commands (NEW)
└── README.md             # Documentation (UPDATED)
```

### Future Files (For 6-Week Refactor)
```
These are saved as reference for your refactoring phase:
├── FUTURE_ARCHITECTURE.md      # Complete microservices structure
├── FUTURE_DOCKER_SETUP.md      # Full Docker guide with Kafka, etc.
```

## 🚀 Quick Start

### 1. Set Up Project Structure

```bash
# Your existing structure:
rtfm-discord-bot/
├── bot.py              ← Already exists
├── database.py         ← Already exists
├── .gitignore          ← Already exists
└── README.md           ← Already exists

# Add the new files:
├── Dockerfile          ← Download and add
├── docker-compose.yml  ← Download and add
├── requirements.txt    ← Download and add
├── .env.example        ← Download and add
└── Makefile           ← Download and add
```

### 2. Copy Files to Your Repo

```bash
# Download all files from outputs folder
# Then copy them to your repo root:

cp Dockerfile ~/your-repo/
cp docker-compose.yml ~/your-repo/
cp requirements.txt ~/your-repo/
cp .env.example ~/your-repo/
cp Makefile ~/your-repo/
cp README.md ~/your-repo/  # Replace existing
```

### 3. Initial Setup

```bash
cd ~/your-repo

# Create .env from template
make setup

# Edit .env with your tokens
nano .env
```

Add your actual tokens:
```bash
DISCORD_TOKEN=your_actual_discord_token
GEMINI_API_KEY=your_actual_gemini_key
GEMINI_API_SECRET=your_actual_gemini_secret
```

### 4. Run with Docker

```bash
# Build and start (all in one)
make init

# Or step by step:
make build    # Build Docker image
make up       # Start bot
make logs     # View logs
```

### 5. Verify It Works

```bash
# Check logs for successful connection
make logs

# You should see:
# "We have logged in as YourBotName#1234"

# Test in Discord:
# Type: RTFM hello
```

## 🛠️ Common Commands

```bash
make help         # Show all commands
make up           # Start bot
make down         # Stop bot
make restart      # Restart bot
make logs         # View live logs
make status       # Check if bot is running
make rebuild      # Rebuild after code changes
make clean        # Stop and remove containers
```

## 📝 Making Code Changes

When you edit `bot.py` or `database.py`:

```bash
# Save your changes
# Then rebuild:
make rebuild

# Check logs:
make logs
```

## 🐛 Troubleshooting

### Bot Won't Start

```bash
# Check logs
make logs

# Common issues:
# - Invalid Discord token → Edit .env
# - Missing Gemini key → Edit .env
# - Port conflicts → make down, then make up
```

### Database Issues

```bash
# Reset database (WARNING: deletes all messages)
make clean-all
make init
```

### Docker Issues

```bash
# Complete reset
make down
docker system prune -f
make build
make up
```

## 📊 Current vs Future Architecture

### What You Have Now (Simple - MVP)

```
┌─────────────────┐
│   Discord Bot   │  ← Single container
│   (bot.py)      │  ← ChromaDB embedded
│   + ChromaDB    │  ← Gemini API calls
└─────────────────┘
```

**Pros:**
- ✅ Simple to understand
- ✅ Easy to deploy
- ✅ Works great for 1 server

**Cons:**
- ❌ Doesn't scale to multiple servers
- ❌ No caching (costs more API calls)
- ❌ Limited monitoring

### What You'll Build (6 Weeks - Scalable)

```
┌──────────┐  ┌─────────┐  ┌──────────┐
│ Discord  │  │  Kafka  │  │Workers x3│
│   Bot    │→ │ Streams │→ │Embedding │
└──────────┘  └─────────┘  └──────────┘
      ↓                            ↓
┌──────────┐  ┌─────────┐  ┌──────────┐
│PostgreSQL│  │  Redis  │  │ ChromaDB │
│Metadata  │  │  Cache  │  │ Vectors  │
└──────────┘  └─────────┘  └──────────┘
      ↓                            ↓
┌──────────┐  ┌─────────┐  ┌──────────┐
│Prometheus│→ │ Grafana │  │  FastAPI │
│ Metrics  │  │Dashboard│  │  Admin   │
└──────────┘  └─────────┘  └──────────┘
```

**Pros:**
- ✅ Scales to 100+ Discord servers
- ✅ Redis caching saves money
- ✅ Background workers handle load
- ✅ Full monitoring & observability
- ✅ Production-ready

**When:**
- 📅 Weeks 1-2: Infrastructure (Kafka, PostgreSQL)
- 📅 Week 3: Microservices separation
- 📅 Week 4: Monitoring (Prometheus, Grafana)
- 📅 Week 5: Advanced features
- 📅 Week 6: Testing & production

## 🎓 Team Roles (For Refactoring Phase)

**Senior Developer:**
- Kafka implementation
- Event streaming architecture

**Dev 1 (DevOps):**
- Docker orchestration
- CI/CD pipelines
- Production deployment

**Dev 2 (Database):**
- PostgreSQL setup
- Redis caching
- Data migrations

**Dev 3 (Discord Bot):**
- Bot command improvements
- Multi-guild support
- Discord integration

**Dev 4 (RAG Pipeline):**
- Embedding optimization
- Vector search improvements
- Gemini prompt engineering

**Dev 5 (Monitoring):**
- Prometheus metrics
- Grafana dashboards
- Alerting system

## 📚 Documentation Files

- **README.md** - Main documentation (current + future plan)
- **FUTURE_ARCHITECTURE.md** - Complete microservices structure
- **FUTURE_DOCKER_SETUP.md** - Full Docker setup with all services
- **.gitignore** - What to exclude from Git

## 🔒 Security Checklist

- ✅ Never commit `.env` file
- ✅ Keep Discord token private
- ✅ Rotate API keys regularly
- ✅ Use `.env.example` for templates only

## 🎯 Next Steps

### For Right Now (This Week)
1. ✅ Add Docker files to your repo
2. ✅ Test bot runs in Docker
3. ✅ Commit to GitHub
4. ✅ Document any issues

### For Refactoring (Weeks 1-6)
1. 📖 Read `FUTURE_ARCHITECTURE.md`
2. 📖 Review `FUTURE_DOCKER_SETUP.md`
3. 🏗️ Follow 6-week timeline
4. 👥 Assign team roles
5. 🚀 Build scalable version

## 💡 Pro Tips

1. **Keep it simple now** - Don't refactor yet, just get Docker working
2. **Save the architecture docs** - You'll need them in weeks 1-6
3. **Test frequently** - Make sure bot works before refactoring
4. **Document changes** - Your team will thank you later
5. **Use Makefile** - Much easier than remembering Docker commands

## 📞 Getting Help

If stuck:
1. Check logs: `make logs`
2. Test connection: `make test-connection`
3. Review README.md
4. Check existing issues on GitHub

---

**Current Status**: 🚧 Setting up Docker for simple structure  
**Next Phase**: 📖 Planning 6-week refactor  
**Goal**: Production-ready multi-server Discord bot
