# RTFM Discord Bot - Repository Structure

## Recommended Folder Structure

```
rtfm-discord-bot/
│
├── .github/                          # GitHub-specific files
│   ├── workflows/                    # CI/CD pipelines
│   │   ├── test.yml                 # Run tests on PR
│   │   ├── build.yml                # Build Docker images
│   │   ├── deploy.yml               # Deploy to production
│   │   └── lint.yml                 # Code quality checks
│   ├── ISSUE_TEMPLATE/              # Issue templates
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── weekly_status.md
│   ├── PULL_REQUEST_TEMPLATE.md     # PR template
│   └── CODEOWNERS                   # Code ownership
│
├── docs/                             # Documentation
│   ├── README.md                    # Overview
│   ├── ARCHITECTURE.md              # System architecture
│   ├── SETUP.md                     # Setup instructions
│   ├── API.md                       # API documentation
│   ├── KAFKA_GUIDE.md              # Kafka implementation
│   ├── RAG_PIPELINE.md             # RAG pipeline details
│   ├── MONITORING.md               # Monitoring guide
│   ├── DEPLOYMENT.md               # Deployment guide
│   ├── TROUBLESHOOTING.md          # Common issues
│   ├── CONTRIBUTING.md             # Contribution guidelines
│   └── diagrams/                   # Architecture diagrams
│       ├── system_overview.png
│       ├── kafka_flow.png
│       └── data_pipeline.png
│
├── src/                             # Source code
│   ├── __init__.py
│   ├── main.py                     # Application entry point
│   │
│   ├── bot/                        # Discord bot
│   │   ├── __init__.py
│   │   ├── client.py              # Discord client
│   │   ├── commands.py            # Slash commands
│   │   ├── events.py              # Event handlers
│   │   └── cogs/                  # Command groups
│   │       ├── __init__.py
│   │       ├── admin.py
│   │       └── rtfm.py
│   │
│   ├── kafka/                      # Kafka integration
│   │   ├── __init__.py
│   │   ├── producer.py            # Message producer
│   │   ├── consumer.py            # Message consumer
│   │   ├── topics.py              # Topic definitions
│   │   └── serializers.py         # Message serialization
│   │
│   ├── rag/                        # RAG pipeline
│   │   ├── __init__.py
│   │   ├── embeddings.py          # Text embeddings
│   │   ├── vectorstore.py         # ChromaDB interface
│   │   ├── retriever.py           # Context retrieval
│   │   ├── generator.py           # Response generation (Gemini)
│   │   └── pipeline.py            # Full RAG pipeline
│   │
│   ├── database/                   # Database layer
│   │   ├── __init__.py
│   │   ├── postgres.py            # PostgreSQL connection
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── migrations/            # Database migrations
│   │   │   └── alembic/
│   │   └── repositories/          # Data access layer
│   │       ├── __init__.py
│   │       ├── guild_repo.py
│   │       └── message_repo.py
│   │
│   ├── cache/                      # Redis caching
│   │   ├── __init__.py
│   │   ├── redis_client.py
│   │   ├── cache_manager.py
│   │   └── strategies.py          # Caching strategies
│   │
│   ├── api/                        # FastAPI (optional web interface)
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   ├── admin.py
│   │   │   └── metrics.py
│   │   └── middleware/
│   │       ├── __init__.py
│   │       └── auth.py
│   │
│   ├── monitoring/                 # Monitoring & metrics
│   │   ├── __init__.py
│   │   ├── prometheus.py          # Prometheus metrics
│   │   ├── logging.py             # Logging configuration
│   │   └── tracer.py              # Distributed tracing
│   │
│   ├── workers/                    # Background workers
│   │   ├── __init__.py
│   │   ├── embedding_worker.py    # Async embedding generation
│   │   ├── indexing_worker.py     # Vector indexing
│   │   └── cleanup_worker.py      # Data cleanup
│   │
│   ├── config/                     # Configuration
│   │   ├── __init__.py
│   │   ├── settings.py            # Settings management
│   │   └── schemas.py             # Configuration schemas
│   │
│   └── utils/                      # Utility functions
│       ├── __init__.py
│       ├── text_processing.py
│       ├── rate_limiter.py
│       └── validators.py
│
├── tests/                           # Test suite
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures
│   ├── unit/                       # Unit tests
│   │   ├── test_embeddings.py
│   │   ├── test_cache.py
│   │   ├── test_vectorstore.py
│   │   └── test_commands.py
│   ├── integration/                # Integration tests
│   │   ├── test_rag_pipeline.py
│   │   ├── test_kafka_flow.py
│   │   └── test_database.py
│   └── e2e/                        # End-to-end tests
│       └── test_bot_flow.py
│
├── docker/                          # Docker configurations
│   ├── Dockerfile.bot              # Bot service
│   ├── Dockerfile.worker           # Worker service
│   ├── Dockerfile.api              # API service (optional)
│   └── docker-compose.yml          # Main compose file
│
├── kubernetes/                      # K8s configs (future)
│   ├── bot-deployment.yaml
│   ├── kafka-statefulset.yaml
│   └── services.yaml
│
├── monitoring/                      # Monitoring configs
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alerts.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── overview.json
│   │   │   ├── kafka.json
│   │   │   └── rag_performance.json
│   │   └── provisioning/
│   │       ├── dashboards.yml
│   │       └── datasources.yml
│   └── loki/                       # Log aggregation (optional)
│       └── loki-config.yml
│
├── scripts/                         # Utility scripts
│   ├── setup.sh                    # Initial setup
│   ├── seed_data.py               # Seed test data
│   ├── backup.sh                  # Backup script
│   ├── migrate.py                 # Database migration
│   └── load_test.py               # Load testing script
│
├── .github/                         # (see above)
├── .gitignore                      # Git ignore file
├── .env.example                    # Environment variables template
├── .dockerignore                   # Docker ignore file
├── docker-compose.yml              # Development compose file
├── docker-compose.prod.yml         # Production compose file
├── requirements.txt                # Python dependencies
├── requirements-dev.txt            # Dev dependencies
├── pyproject.toml                  # Project metadata (Poetry/setuptools)
├── pytest.ini                      # Pytest configuration
├── .pre-commit-config.yaml         # Pre-commit hooks
├── Makefile                        # Common commands
├── README.md                       # Project README
├── LICENSE                         # Project license
└── CHANGELOG.md                    # Version changelog
```

## Key Files to Create First

### 1. README.md (Root)
```markdown
# RTFM - Discord Memory Bot

> Real-time event-driven Discord bot using Apache Kafka, Docker Swarm, and RAG

## Quick Start

\`\`\`bash
# Clone the repository
git clone https://github.com/yourusername/rtfm-discord-bot.git

# Copy environment variables
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f bot
\`\`\`

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP.md)
- [API Documentation](docs/API.md)

## Features

- 🚀 Event-driven architecture with Apache Kafka
- 🤖 Multi-tenant Discord bot
- 🧠 RAG-powered semantic search
- 📊 Prometheus + Grafana monitoring
- 🐳 Docker Swarm orchestration
- 🔄 CI/CD with GitHub Actions

## Tech Stack

- Python 3.11+
- Discord.py 2.0
- Apache Kafka
- PostgreSQL
- ChromaDB
- Redis
- Google Gemini API

## Team

- **Senior Developer**: Kafka implementation
- **Dev 1**: DevOps & Docker
- **Dev 2**: Database & PostgreSQL
- **Dev 3**: Discord Bot
- **Dev 4**: RAG Pipeline
- **Dev 5**: Monitoring
```

### 2. .env.example
```bash
# Discord
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_APP_ID=your_app_id_here

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# Kafka
KAFKA_BOOTSTRAP_SERVERS=kafka:9092
KAFKA_TOPIC_MESSAGES=discord_messages
KAFKA_TOPIC_EMBEDDINGS=discord_embeddings
KAFKA_CONSUMER_GROUP=rtfm_bot

# PostgreSQL
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=rtfm
POSTGRES_USER=rtfm_user
POSTGRES_PASSWORD=change_this_password

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=change_this_password

# ChromaDB
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# Monitoring
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=admin

# Application
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### 3. docker-compose.yml
```yaml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    ports:
      - "9092:9092"
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    volumes:
      - kafka-data:/var/lib/kafka/data

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"

  chromadb:
    image: chromadb/chroma:latest
    volumes:
      - chroma-data:/chroma/chroma
    ports:
      - "8000:8000"

  bot:
    build:
      context: .
      dockerfile: docker/Dockerfile.bot
    depends_on:
      - kafka
      - postgres
      - redis
      - chromadb
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    env_file:
      - .env

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus:/etc/prometheus
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    depends_on:
      - prometheus
    volumes:
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - grafana-data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD}
    ports:
      - "3000:3000"

volumes:
  zookeeper-data:
  kafka-data:
  postgres-data:
  redis-data:
  chroma-data:
  prometheus-data:
  grafana-data:
```

### 4. Makefile
```makefile
.PHONY: help install test lint format clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linters"
	@echo "  make format        - Format code"
	@echo "  make docker-up     - Start Docker services"
	@echo "  make docker-down   - Stop Docker services"
	@echo "  make clean         - Clean cache files"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

test:
	pytest tests/ -v --cov=src

lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	rm -rf .pytest_cache .coverage htmlcov/
```

## GitHub Branch Strategy

```
main                  # Production-ready code
├── develop          # Development branch
    ├── feature/kafka-integration
    ├── feature/rag-pipeline
    ├── feature/monitoring
    ├── feature/docker-setup
    └── feature/testing
```

## Recommended GitHub Settings

1. **Branch Protection Rules** (for `main`):
   - Require pull request reviews (at least 1)
   - Require status checks to pass
   - Require linear history
   - Do not allow force pushes

2. **Required Status Checks**:
   - Tests must pass
   - Linting must pass
   - Docker build must succeed

3. **GitHub Actions Secrets**:
   - `DISCORD_TOKEN`
   - `GEMINI_API_KEY`
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`

## Initial Setup Steps

1. **Create the repository structure**:
```bash
mkdir -p {src/{bot,kafka,rag,database,cache,api,monitoring,workers,config,utils},tests/{unit,integration,e2e},docker,monitoring/{prometheus,grafana},scripts,docs}
```

2. **Initialize Git**:
```bash
git init
git add .
git commit -m "Initial project structure"
```

3. **Create and push to GitHub**:
```bash
git remote add origin https://github.com/yourusername/rtfm-discord-bot.git
git branch -M main
git push -u origin main
```

4. **Create development branch**:
```bash
git checkout -b develop
git push -u origin develop
```

5. **Set up pre-commit hooks** (optional but recommended):
```bash
pip install pre-commit
pre-commit install
```
