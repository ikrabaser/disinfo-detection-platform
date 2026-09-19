# Social Media Disinformation & Fake News Detection Platform

## Project Goal

Fake news and manipulative content spreading on social media platforms will
be detected not only through text analysis, but through a model that
focuses on the news' propagation graph. As part of this project, who
shared the news, the interaction networks between users, and the speed of
propagation will be modeled using Graph Neural Networks (GNN). While
Natural Language Processing (NLP) techniques handle semantic analysis of
the text, GNN will analyze whether the news was spread in an organized way
by "bot" accounts. The system will be trained to fit Turkish language
structure and will produce a real-time truth score by pulling live data
from platforms such as Twitter (X).

This repository contains the **skeleton** of the above graduation-project
idea: the full directory structure, interfaces, and configuration reflect
the intended full technology stack, but heavy ML training and real X
(Twitter) API calls are **out of scope** and have been replaced with
mock/stub data (marked as `TODO` in the code).

## Tech Stack

**Frontend:** React + TypeScript + Vite + Tailwind CSS + Recharts (charts)
+ Cytoscape.js (propagation network visualization)

**Backend:** Python + Django + Django REST Framework + Django ORM

**Auth & Security:** Django auth, JWT via HttpOnly cookie
(`rest_framework_simplejwt`), simple RBAC (roles: `admin`, `analyst`,
`viewer`), DRF throttling, tool-level permission system for the AI agent.

**AI Agent Layer:** the `agent` Django app wraps the OpenAI Agents SDK /
OpenAI API (`openai` package) with tool-calling. Tools: `get_news`,
`get_social_posts`, `run_nlp_analysis`, `run_gnn_analysis`,
`run_bot_analysis`, `verify_sources`, `get_analysis_result`.

**NLP / ML:** the `nlp_engine` app - stub interfaces for PyTorch, Hugging
Face Transformers, Sentence Transformers, scikit-learn (`TextClassifier`,
`EmbeddingService`).

**Graph/GNN:** the `graph_engine` app - propagation graph construction with
PyTorch Geometric + NetworkX, GCN/GAT/GraphSAGE model skeletons
(`graph_engine/models/`).

**Data Processing:** `data_processing` - a pandas/numpy-based utility
module.

**Database:** PostgreSQL (Django ORM, `DATABASE_URL`), optional `pgvector`
note (as a comment in `analyses/models.py`).

**Background Processing:** Procrastinate (optional, `PROCRASTINATE_ENABLED`).

**Real-Time:** the `realtime` app - Centrifugo integration, Redis backing
store.

**External Data:** the `external` app - X API client (mock), news source
fetcher (mock), Higgsfield client (mock) - for generating shareable
summary images/videos from analysis results.

**Infrastructure:** Dockerfile (backend/frontend), `docker-compose.yml`,
`infra/nginx.conf`, gunicorn entrypoint.

**Monitoring:** Sentry DSN note, Prometheus metrics endpoint stub,
`grafana/` placeholder dashboard.

## Directory Structure (summary)

```
backend/
  core/                # Django project settings (settings, urls, wsgi, asgi)
  accounts/            # Auth + RBAC (custom User model, roles)
  agent/                # AI agent layer (OpenAI wrapper + tools)
    tools/              # get_news, get_social_posts, run_nlp_analysis, ...
  nlp_engine/           # TextClassifier, EmbeddingService (stub)
  graph_engine/         # PropagationGraph model + GCN/GAT/GraphSAGE stubs
    models/
  data_processing/      # pandas/numpy helpers (plain Python package)
  analyses/             # Analysis model (main model tying all results together)
  realtime/             # Centrifugo client, SSE/WebSocket notes
  external/             # X API client (mock), news fetcher (mock), Higgsfield client (mock)
  procrastinate_app/    # Optional async task queue (stub)
  requirements.txt
  pytest.ini
frontend/
  src/
    api/client.ts       # HttpOnly cookie based axios client
    pages/               # Dashboard, AnalysisDetail, Login
    components/          # ScoreTrendChart (Recharts), PropagationGraph (Cytoscape)
infra/
  nginx.conf
grafana/
  dashboards/placeholder-dashboard.json
.github/workflows/ci.yml
docker-compose.yml
```

## Setup & Running

### Backend (Django)

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit values if needed
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

> Note: if `DATABASE_URL` is not set, or `dj-database-url`/`psycopg` is not
> installed, the settings file automatically falls back to SQLite - so the
> skeleton can be verified with `python manage.py check` even without
> PostgreSQL installed.

### Tests

```bash
cd backend
pytest
```

### Frontend (Vite + React)

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Docker Compose (full system)

```bash
docker compose config   # validate configuration
docker compose up --build
```

## Deliberately Left Unimplemented (TODO)

- **Real GNN training/inference**: the `forward()` methods in
  `graph_engine/models/*.py` return mock results; real `torch_geometric`
  layers have not been written.
- **Real NLP model**: `nlp_engine/text_classifier.py` and
  `embedding_service.py` use heuristic/hash-based mock logic; a real
  fine-tuned Turkish model (e.g. BERTurk) has not been integrated.
- **Real X (Twitter) API calls**: `external/x_client.py` returns entirely
  mock data; real `tweepy`/HTTP integration has not been done.
- **Real Higgsfield API calls**: `external/higgsfield_client.py` returns
  entirely mock data; no real image/video generation request is sent.
- **Real OpenAI Agents SDK integration**: `agent/client.py` returns a mock
  response when `OPENAI_API_KEY` is empty; the real tool-calling
  (function calling loop) has not been implemented.
- **Real Procrastinate setup**: `procrastinate_app/` is a stub; the real
  worker process and Postgres-backed queue are not active
  (`PROCRASTINATE_ENABLED=false`).
- **Real Centrifugo publishing**: `realtime/centrifugo_client.py` does not
  actually send the HTTP request, it only logs.
- **pgvector**: left as a comment in `analyses/models.py`, not active.
- **Prometheus/Sentry**: the `django-prometheus` and `sentry-sdk` packages
  are commented out in `requirements.txt`; no real setup has been done.

## Role-Based Access Control (RBAC)

| Role     | Permissions                                                |
|----------|-------------------------------------------------------------|
| admin    | All operations (including user management)                 |
| analyst  | Create/run analyses, most of the AI agent tools             |
| viewer   | Read-only view only                                         |

Each AI agent tool (`agent/tools/*.py`) declares which roles can call it
via the `@tool_permission(roles={...})` decorator.
