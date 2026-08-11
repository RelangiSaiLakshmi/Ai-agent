# AI Agent Coordination & Decision Engine — API image (Milestone 4).
#
# Builds a single image that can run either the REST API or the dashboard:
#   docker build -t ai-coordination .
#   docker run -p 8000:8000 ai-coordination                      # API (default)
#   docker run -p 8501:8501 ai-coordination \
#       streamlit run frontend/dashboard.py --server.address 0.0.0.0
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    LLM_PROVIDER=mock \
    DB_PATH=/data/app.db

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Seed the bundled SQLite database into the mounted data volume at build time.
RUN mkdir -p /data

EXPOSE 8000 8501

# Default command: serve the REST API. Override the CMD to run the dashboard.
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
