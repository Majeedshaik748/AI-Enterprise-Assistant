# Enterprise AI Knowledge Assistant

A production-shaped RAG (Retrieval-Augmented Generation) system: upload
PDFs, Word docs, PowerPoint decks, and spreadsheets, then ask questions in
plain language and get answers with the exact source passage cited.

Built to demonstrate end-to-end product engineering: system design, a real
backend, AI integration, a relational + vector data layer, containerized
deployment, CI, tests, and a usable UI — not just a model wrapper.

## Features

- **Multi-format ingestion** — PDF, DOCX, PPTX, XLSX/CSV
- **Cited Q&A** — every answer links back to the document, chunk, and
  similarity score it was drawn from
- **Document summarization** and **document comparison**
- **Report generation** across multiple documents
- **JWT auth** with access + refresh tokens; first registered user
  becomes workspace admin
- **Admin panel** — usage stats, index status breakdown, user list
- **IBM watsonx.ai-ready** — pluggable LLM provider (`watsonx` /
  `huggingface` / `mock`), so it runs immediately with zero API keys and
  drops in watsonx credentials for production
- Structured JSON logging, global error handling, health checks
- Dockerized, with CI running backend tests + both Docker builds on every push

## Tech stack

| Layer          | Choice                                   |
|----------------|-------------------------------------------|
| Backend        | FastAPI, SQLAlchemy, Pydantic             |
| Database       | PostgreSQL                                |
| Vector store   | ChromaDB (swappable for FAISS)            |
| RAG / AI       | LangChain-compatible pipeline, watsonx.ai / Hugging Face |
| Frontend       | Next.js (App Router), React, Tailwind CSS |
| Auth           | JWT (access + refresh)                    |
| Infra          | Docker, Docker Compose, GitHub Actions CI |

See [`docs/architecture.md`](docs/architecture.md) for the full system
design and data flow diagrams.

## Project structure

```
AI-Enterprise-Assistant/
├── backend/            FastAPI app, RAG services, tests
│   ├── app/
│   │   ├── api/routes/ auth, documents, query (RAG), admin
│   │   ├── core/       config, security (JWT, hashing)
│   │   ├── db/         SQLAlchemy models + session
│   │   ├── schemas/    Pydantic request/response models
│   │   └── services/   document parsing, embeddings/LLM, vector store, RAG orchestration
│   └── tests/          pytest suite (auth, documents, RAG endpoints)
├── frontend/           Next.js app (login, dashboard, chat, admin)
├── docker-compose.yml  Postgres + backend + frontend
├── .github/workflows/  CI: tests, lint, Docker builds
└── docs/architecture.md
```

## Running locally

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/api/docs

### Option B — run services individually

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL to point at a local Postgres, or use SQLite for a quick spin
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

By default `LLM_PROVIDER=mock`, so the entire pipeline — upload, chunk,
embed, retrieve, cite — runs with **zero external API keys**. To use real
generation, set in `backend/.env`:

```
LLM_PROVIDER=watsonx
WATSONX_API_KEY=...
WATSONX_PROJECT_ID=...
```

or `LLM_PROVIDER=huggingface` with `HUGGINGFACEHUB_API_TOKEN` set.

## Running tests

```bash
cd backend
pip install -r requirements.txt
pytest
```

Tests run against an in-memory SQLite database and the mock LLM provider,
so they require no external services and run in a few seconds — this is
also what CI runs on every push.

## API surface

| Endpoint                          | Description                          |
|------------------------------------|---------------------------------------|
| `POST /api/v1/auth/register`       | Create account (first user = admin)   |
| `POST /api/v1/auth/login`          | Get access + refresh tokens           |
| `POST /api/v1/auth/refresh`        | Rotate tokens                         |
| `POST /api/v1/documents/upload`    | Upload + async-index a document       |
| `GET /api/v1/documents`            | List your documents                   |
| `POST /api/v1/query`               | Ask a question, get a cited answer    |
| `POST /api/v1/summarize`           | Summarize a document                  |
| `POST /api/v1/compare`             | Compare two documents                 |
| `POST /api/v1/report`              | Generate a report across documents    |
| `GET /api/v1/admin/stats`          | Workspace usage stats (admin only)    |

Full interactive docs at `/api/docs` once the backend is running.

## Notes on scope

This is a portfolio-grade scaffold, not a finished commercial product.
Things intentionally left as "next steps" rather than built out fully:
Alembic migrations (SQLAlchemy `create_all` is used for simplicity),
a real task queue for ingestion at scale, rate limiting, and multi-tenant
workspace isolation. These are called out explicitly in
`docs/architecture.md` under "Scaling to production" — flagging them is
part of demonstrating product judgment, not a gap to hide.
