# Docker Setup Guide for RTFM

## Prerequisites

- Docker 24.0+ installed
- Docker Compose 2.20+ installed
- At least 8GB RAM available for Docker
- 20GB free disk space

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/rtfm-discord-bot.git
cd rtfm-discord-bot
```

### 2. Set Up Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required Variables:**
```bash
# Discord Bot Token (get from https://discord.com/developers/applications)
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_APP_ID=your_application_id_here

# Gemini API Key (get from https://makersuite.google.com/app/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# Database Passwords (change these!)
POSTGRES_PASSWORD=your_secure_password_here
REDIS_PASSWORD=your_secure_password_here
GRAFANA_ADMIN_PASSWORD=your_secure_password_here
```

### 3. Create Required Directories

```bash
# Create directories for scripts
mkdir -p scripts

# Move entrypoint scripts to scripts directory
mv entrypoint.sh scripts/
mv worker-entrypoint.sh scripts/
mv api-entrypoint.sh scripts/
mv wait-for-it.sh scripts/

# Make scripts executable
chmod +x scripts/*.sh

# Create monitoring directories
mkdir -p monitoring/prometheus
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning

# Create logs directory
mkdir -p logs
```

### 4. Build Docker Images

```bash
# Build all images
docker-compose build

# Or build specific services
docker-compose build bot
docker-compose build embedding-worker
docker-compose build indexing-worker
```

### 5. Start Services

```bash
# Start all services in detached mode
docker-compose up -d

# Or start specific services
docker-compose up -d postgres redis chromadb kafka
docker-compose up -d bot
```

### 6. Verify Services are Running

```bash
# Check status of all containers
docker-compose ps

# Check logs
docker-compose logs -f

# Check specific service logs
docker-compose logs -f bot
docker-compose logs -f kafka
```

## Common Commands

### Service Management

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a specific service
docker-compose restart bot

# Stop and remove all containers, networks, and volumes
docker-compose down -v

# View logs in real-time
docker-compose logs -f

# View logs for specific service
docker-compose logs -f bot

# Execute command in running container
docker-compose exec bot bash

# Scale workers
docker-compose up -d --scale embedding-worker=3
```

### Building & Rebuilding

```bash
# Rebuild after code changes
docker-compose build bot
docker-compose up -d bot

# Force rebuild without cache
docker-compose build --no-cache bot

# Pull latest base images
docker-compose pull
```

### Database Operations

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U rtfm_user -d rtfm

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U rtfm_user rtfm > backup.sql

# Restore PostgreSQL
docker-compose exec -T postgres psql -U rtfm_user rtfm < backup.sql

# Access Redis CLI
docker-compose exec redis redis-cli -a your_redis_password

# Monitor Redis
docker-compose exec redis redis-cli -a your_redis_password MONITOR
```

### Monitoring

```bash
# Access Grafana
# Open browser to: http://localhost:3000
# Default credentials: admin / admin (change in .env)

# Access Prometheus
# Open browser to: http://localhost:9090

# Access Kafka UI (if enabled)
# Open browser to: http://localhost:8080
```

## Troubleshooting

### Services Won't Start

```bash
# Check logs for errors
docker-compose logs

# Check if ports are already in use
netstat -tulpn | grep LISTEN

# Remove old containers and volumes
docker-compose down -v
docker-compose up -d
```

### Out of Memory

```bash
# Check Docker memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Recommended: 8GB minimum

# Clean up unused resources
docker system prune -a
```

### Bot Won't Connect to Discord

```bash
# Verify token is correct in .env
cat .env | grep DISCORD_TOKEN

# Check bot logs
docker-compose logs bot

# Restart bot service
docker-compose restart bot
```

### Kafka Issues

```bash
# Check Kafka logs
docker-compose logs kafka

# Verify Kafka is healthy
docker-compose exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# List topics
docker-compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Check consumer groups
docker-compose exec kafka kafka-consumer-groups --list --bootstrap-server localhost:9092
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
docker-compose exec postgres pg_isready -U rtfm_user

# Check PostgreSQL logs
docker-compose logs postgres

# Reset PostgreSQL (WARNING: deletes all data)
docker-compose down -v
docker volume rm rtfm-postgres-data
docker-compose up -d postgres
```

## Development Workflow

### Making Code Changes

```bash
# 1. Make changes to code
vim src/bot/client.py

# 2. Rebuild the specific service
docker-compose build bot

# 3. Restart the service
docker-compose up -d bot

# 4. Check logs
docker-compose logs -f bot
```

### Adding New Dependencies

```bash
# 1. Add to requirements.txt
echo "new-package==1.0.0" >> requirements.txt

# 2. Rebuild all images that need it
docker-compose build --no-cache

# 3. Restart services
docker-compose up -d
```

### Running Tests

```bash
# Run tests in a container
docker-compose run --rm bot pytest tests/

# Run with coverage
docker-compose run --rm bot pytest tests/ --cov=src --cov-report=html

# Run specific test file
docker-compose run --rm bot pytest tests/unit/test_embeddings.py
```

## Production Deployment

### Using Docker Compose in Production

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With resource limits
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale embedding-worker=3
```

### Using Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml rtfm

# Check services
docker service ls

# Scale services
docker service scale rtfm_embedding-worker=5

# View logs
docker service logs rtfm_bot
```

## Health Checks

All services include health checks. Check them with:

```bash
# View health status
docker-compose ps

# Detailed inspection
docker inspect rtfm-bot | grep -A 10 Health

# Manual health check
docker-compose exec bot python -c "import sys; sys.exit(0)"
```

## Performance Tuning

### Kafka Optimization

Edit `docker-compose.yml`:
```yaml
kafka:
  environment:
    KAFKA_NUM_PARTITIONS: 6
    KAFKA_DEFAULT_REPLICATION_FACTOR: 1
    KAFKA_LOG_RETENTION_HOURS: 24
```

### PostgreSQL Optimization

```bash
# Access PostgreSQL config
docker-compose exec postgres bash

# Edit postgresql.conf
# Increase shared_buffers, max_connections, etc.
```

### Redis Optimization

```yaml
redis:
  command: >
    redis-server
    --maxmemory 2gb
    --maxmemory-policy allkeys-lru
```

## Cleaning Up

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Complete cleanup
docker system prune -a --volumes
```

## Monitoring Disk Space

```bash
# Check Docker disk usage
docker system df

# Detailed view
docker system df -v

# Clean up build cache
docker builder prune
```

## Security Best Practices

1. **Never commit .env files** - Always use .env.example as template
2. **Use strong passwords** - Change all default passwords
3. **Limit exposed ports** - Only expose what's necessary
4. **Regular updates** - Keep base images updated
5. **Non-root users** - All Dockerfiles use non-root users
6. **Read-only filesystems** - Consider adding read_only: true where possible

## Next Steps

1. Set up [GitHub Actions CI/CD](.github/workflows/)
2. Configure [Grafana Dashboards](monitoring/grafana/)
3. Review [Architecture Documentation](docs/ARCHITECTURE.md)
4. Set up [Backup Strategy](docs/BACKUP.md)

## Support

- Check [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- Review [FAQ](docs/FAQ.md)
- Open an issue on GitHub
