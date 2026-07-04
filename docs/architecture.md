# Architecture

## Overview

The Enterprise AI Knowledge Assistant is a Retrieval-Augmented Generation
(RAG) system. Documents are chunked, embedded, and stored in a vector
database; questions are answered by retrieving the most relevant chunks and
passing them to an LLM as grounding context, with every answer traced back
to its source chunk.

```
┌─────────────┐      HTTPS/JSON      ┌──────────────┐
│  Next.js UI │ ───────────────────▶ │   FastAPI    │
│  (React)    │ ◀─────────────────── │   Backend    │
└─────────────┘                      └──────┬───────┘
                                             │
                     ┌───────────────────────┼───────────────────────┐
                     ▼                       ▼                       ▼
             ┌───────────────┐      ┌────────────────┐      ┌────────────────┐
             │  PostgreSQL   │      │   ChromaDB      │      │  LLM Provider   │
             │  (users,      │      │  (vector store  │      │  watsonx.ai /   │
             │   documents,  │      │   of chunk      │      │  HuggingFace /  │
             │   query logs) │      │   embeddings)   │      │  local mock     │
             └───────────────┘      └────────────────┘      └────────────────┘
```

## Request flow: asking a question

1. Client sends `POST /api/v1/query` with a JWT and a question.
2. FastAPI validates the token (`app/api/deps.py`) and resolves the user.
3. `rag_service.answer_question` embeds the question, queries ChromaDB for
   the top-k nearest chunks (optionally scoped to specific document IDs),
   and assembles a grounding prompt.
4. The prompt is sent to the configured LLM provider (`llm_provider.py`).
5. The answer and its source chunks (document, page/chunk index, similarity
   score) are returned together and logged to `query_logs` for admin
   analytics.

## Request flow: uploading a document

1. Client sends a multipart upload to `POST /api/v1/documents/upload`.
2. The file is validated (extension, size) and saved to disk; a `Document`
   row is created with status `pending`.
3. A FastAPI `BackgroundTask` processes the file asynchronously:
   extract text → chunk → embed → write to ChromaDB → mark `indexed`.
4. The frontend polls `GET /api/v1/documents` to reflect status changes in
   near real time without needing websockets.

## Why these choices

- **FastAPI** — async-first, automatic OpenAPI docs, strong typing via
  Pydantic; the standard choice for production Python APIs.
- **PostgreSQL** — durable relational store for users, document metadata,
  and audit logs. Vector data is kept separate from relational data so
  either can scale independently.
- **ChromaDB** — embedded, disk-persisted vector store with zero external
  infra to run locally; the `vector_store.py` module isolates it behind a
  small interface so it can be swapped for FAISS or a managed vector DB
  (e.g. watsonx.data, Pinecone) without touching the RAG logic.
- **Pluggable LLM provider** — `LLM_PROVIDER` env var switches between IBM
  watsonx.ai (`ibm-watsonx-ai` SDK), Hugging Face Inference, or a
  deterministic offline mock. The mock exists so the entire product —
  upload, index, ask, cite — is demoable and testable with zero API keys
  or cost, which is also what keeps CI fast and free.
- **JWT with access + refresh tokens** — stateless auth suitable for
  horizontal scaling; refresh tokens let the frontend silently renew
  sessions without forcing re-login every hour.
- **Background tasks for ingestion** — keeps the upload request fast; for
  higher throughput this is the natural place to swap in a real task
  queue (Celery/RQ + Redis) without changing the API contract.

## Data model

- `users` — email, hashed password, role (`admin`/`user`).
- `documents` — owner, filename, type, storage path, status
  (`pending`/`processing`/`indexed`/`failed`), summary cache.
- `chunks` — metadata mirror of what's stored in the vector DB, used for
  admin/debug visibility without querying Chroma directly.
- `query_logs` — every question asked, its answer, cited sources, and
  latency, for usage analytics in the admin panel.

## Scaling to production

- Swap `Base.metadata.create_all` for Alembic migrations (scaffolded via
  the `alembic` dependency) before any real deployment.
- Move background ingestion to a proper task queue once upload volume
  exceeds what in-process background tasks can handle.
- Put the API behind a managed load balancer / API gateway; the app is
  already stateless aside from the database and vector store, so it scales
  horizontally.
- Swap ChromaDB's local persistence for a managed vector database if
  multi-node access to the same index is required.
