# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — Market Research & Synthesis Engine
#
# Build:  docker build -t market-research-engine .
# Run:    docker run -p 8501:8501 --env-file .env market-research-engine
# ─────────────────────────────────────────────────────────────────────────────

# Use official slim Python image (smaller than full python:3.11)
FROM python:3.11-slim

# ── System dependencies ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    cron \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Working directory ────────────────────────────────────────────────────────
WORKDIR /app

# ── Copy requirements first (layer caching — faster rebuilds) ────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy all project files ───────────────────────────────────────────────────
COPY . .

# ── Create output directory ──────────────────────────────────────────────────
RUN mkdir -p output

# ── Set up daily cron job (runs pipeline at 7 AM every day) ─────────────────
# This calls main.py using the RESEARCH_TOPIC from the .env file
RUN echo "0 7 * * * cd /app && python main.py >> /app/output/cron.log 2>&1" \
    > /etc/cron.d/research-cron \
    && chmod 0644 /etc/cron.d/research-cron \
    && crontab /etc/cron.d/research-cron

# ── Expose Streamlit port ────────────────────────────────────────────────────
EXPOSE 8501

# ── Health check ─────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# ── Entrypoint: start cron daemon + Streamlit ────────────────────────────────
CMD cron && streamlit run app.py \
    --server.port=8501 \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
