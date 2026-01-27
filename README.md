## AI-Powered Intelligence Digest System

Local-first news intelligence platform that ingests multiple public sources, filters them with small language models that run on Ollama, and ships persona-aware digests by email/Telegram. This repository currently focuses on Phase 1: resilient data ingestion into PostgreSQL, ready for downstream vector search and summarization.

### Tech Stack
- Python 3.11+ managed with `uv`
- PostgreSQL + SQLAlchemy (pgvector/FAISS to be added later)
- httpx + feedparser for ingestion
- Typer CLI, structlog logging
- Ollama (Llama 3.x 8B Instruct Q4) for future on-device summarization

### Getting Started
1. **Install tooling**
	- `pip install uv` (or follow <https://github.com/astral-sh/uv>)
	- Install PostgreSQL locally and create a database: `createdb dailydigest`
	- Install Ollama and pull a lightweight Llama 3 model (`ollama pull llama3:8b-instruct-q4_K_M`).
2. **Clone + install deps**
	```bash
	uv sync
	```
3. **Configure environment**
	```bash
	cp .env.example .env
	# edit database credentials, RSS feeds, persona toggles, etc.
	```
4. **Run a scrape**
	```bash
	uv run dailydigest-scrape run --sources hackernews,rss --hours 24
	```
	List adapters anytime with `uv run dailydigest-scrape sources`. Each run fetches new items, deduplicates them, and stores results in PostgreSQL with structured logging output.

### Roadmap
1. **Phase 1 – Data foundation**: source adapters, dedupe, Postgres storage (in progress).
2. **Phase 2 – Vector + LLM eval**: embeddings via FAISS/pgvector, local Llama scoring, schema validation.
3. **Phase 3 – Persona workflows**: GENAI_NEWS and PRODUCT_IDEAS clustering/summarization pipelines.
4. **Phase 4 – Delivery & scheduling**: HTML email + Telegram delivery, cron/systemd automation, observability.

Progress is incremental—please keep the scope limited to one phase at a time.
