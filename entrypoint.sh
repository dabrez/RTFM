#!/bin/bash
# ============================================================================
# RTFM Discord Bot - Docker Entrypoint (Simplified)
# ============================================================================

set -e

echo "Starting RTFM Services..."

# Start Dashboard in the background
echo "Starting Dashboard on port ${PORT:-8080}..."
uvicorn dashboard.main:app --host 0.0.0.0 --port ${PORT:-8080} &

# Start Bot in the foreground
echo "Starting Discord Bot..."
python bot.py

# Wait for all background processes to finish
wait
