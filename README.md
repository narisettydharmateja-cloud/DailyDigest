# DailyDigest

Local-first news intelligence platform that ingests public sources, stores structured items in PostgreSQL, and supports subscription delivery via a FastAPI backend and React frontend. Phase 1 focuses on resilient ingestion and storage, with later phases enabling ranking, clustering, and delivery.

## Tech Stack

**Backend**
- Python 3.11+ managed with `uv`
- PostgreSQL + SQLAlchemy
- FastAPI for subscription API
- httpx + feedparser for ingestion
- Typer CLI, structlog logging
- Ollama (Llama 3.x 8B Instruct Q4) for future on-device summarization

**Frontend**
- React 18 + Vite
- Axios for API calls
- CSS3 custom styling

## Project Structure

```
api_server.py               # FastAPI subscription API
frontend/                   # React frontend (Vite)
src/dailydigest/            # Backend library + CLI
```

## Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL
- `uv` package manager (`pip install uv`)

## Backend Setup

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# update DATABASE_URL, SMTP settings, RSS feeds, etc.
```

3. Run the FastAPI server:
```bash
uv run python api_server.py
```

The API will be available at http://localhost:8000

### API Endpoints

- `GET /` — health check
- `POST /api/subscribe` — create or update a subscription
  - Body: `{ "email": "user@example.com", "categories": ["genai"], "frequency": "daily" }`
- `GET /api/subscriptions` — list active subscriptions
- `DELETE /api/subscribe/{email}` — unsubscribe

### Ingestion CLI

Run a scrape:
```bash
uv run dailydigest-scrape run --sources hackernews,rss --hours 24
```

List adapters:
```bash
uv run dailydigest-scrape sources
```

## Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the dev server:
```bash
npm run dev
```

The app will open at http://localhost:3000 and will proxy API requests to http://localhost:8000.

## Running Both

Use two terminals:

Terminal 1 (backend):
```bash
uv run python api_server.py
```

Terminal 2 (frontend):
```bash
cd frontend
npm run dev
```

## Roadmap

1. **Phase 1 – Data foundation**: source adapters, dedupe, Postgres storage (in progress).
2. **Phase 2 – Vector + LLM eval**: embeddings via FAISS/pgvector, local Llama scoring, schema validation.
3. **Phase 3 – Persona workflows**: GENAI_NEWS and PRODUCT_IDEAS clustering/summarization pipelines.
4. **Phase 4 – Delivery & scheduling**: HTML email + Telegram delivery, cron/systemd automation, observability.

Progress is incremental—please keep the scope limited to one phase at a time.
