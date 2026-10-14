# ==============================================================================
# Multi-Stage Production Dockerfile for Workflow Mining Agent
# AI Builder Cup 2026 - Cloud Run Deployment
# ==============================================================================

# Stage 1: Build React Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python API & Web Server
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install system dependencies for scientific libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, SQL scripts, generator scripts, and initial data
COPY backend/ ./backend/
COPY sql/ ./sql/
COPY scripts/ ./scripts/
COPY data/ ./data/

# Copy built frontend assets from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set Cloud Run production environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV APP_MODE=CLOUD
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Launch FastAPI via Uvicorn
CMD ["sh", "-c", "uvicorn backend.api.app:app --host 0.0.0.0 --port ${PORT}"]
