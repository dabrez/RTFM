# ============================================================================ 
# RTFM Discord Bot - Dockerfile (Simplified)
# ============================================================================ 
# Stage 1: Builder
# ============================================================================ 
FROM python:3.11 as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================================ 
# Stage 2: Final Image
# ============================================================================ 
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FASTEMBED_CACHE_PATH=/app/model_cache

# Set working directory
WORKDIR /app

# Copy the virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application files
COPY bot.py .
COPY database.py .
COPY utils.py .
COPY entrypoint.sh .
COPY dashboard/ dashboard/

# Install runtime dependencies (e.g., for fastembed/onnx and postgres)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    libpq5 \
    libstdc++6 \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Make entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Create directories for database and logs
RUN mkdir -p /app/discord_db /app/logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "bot.py"]
