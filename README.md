# VERITAS — Social Media Disinformation Detection Platform

VERITAS is a graduation-project platform for detecting and analysing misinformation signals on social media by combining **Natural Language Processing (NLP)** with **Graph Neural Networks (GNN)**.

Instead of relying only on the text of a claim, VERITAS also analyses how content propagates through a social network. The current architecture evaluates textual signals and propagation behaviour independently, then presents these outputs as separate analysis signals.

The platform includes:

- Turkish text classification with a fine-tuned BERTurk model
- propagation graph construction from social-media data
- PyTorch Geometric based GNN inference
- PostgreSQL-backed asynchronous processing with Procrastinate
- realtime analysis progress with Centrifugo
- Cytoscape.js network visualisation
- JWT-based authentication and role-based access
- professional light/dark React dashboard
- GitHub Actions CI/CD
- Docker container delivery through GitHub Container Registry

> **Important methodological note:**  
> The current GNN model was trained on **UPFD / PolitiFact**, which is not a Turkish X dataset. Therefore, applying the model to Turkish X data is currently treated as a **cross-domain experimental signal** and must not be interpreted as a calibrated truth probability.

---

# System Overview

The current analysis flow is:

```text
User
  │
  ▼
React Frontend
  │
  │ REST / JWT
  ▼
Django REST API
  │
  ▼
Analysis record
  │
  ▼
PostgreSQL
  │
  ▼
Procrastinate Queue
  │
  ▼
Background Worker
  │
  ├── NLP Classification
  │     └── BERTurk / heuristic fallback
  │
  ├── Social Data Ingestion
  │     └── X API v2 / mock fallback
  │
  ├── Propagation Graph Construction
  │
  ├── GNN Inference
  │     └── Aligned GCN
  │
  ├── Bot Analysis
  │     └── Experimental / mock
  │
  └── Persist Results
          │
          ▼
     Centrifugo
          │
          ▼
Realtime progress events
          │
          ▼
React Analysis Detail UI
```

The complete machine-learning workflow is **not executed synchronously inside the HTTP request**.

Instead, Django creates the analysis record and queues a background job. A Procrastinate worker executes the expensive analysis stages independently.

This keeps request latency separate from ML inference latency and provides a more scalable architecture.

---

# Current Analysis Pipeline

The current asynchronous analysis pipeline runs through the following stages:

```text
5%    Analysis started
15%   NLP
35%   Propagation graph
60%   GNN
80%   Bot analysis
100%  Completed
```

Progress events are published to Centrifugo and displayed in realtime on the frontend.

The system currently **does not calculate a combined truth score**.

This is intentional because:

```text
GNN signal
    +
experimental bot signal
    +
uncalibrated model confidence
    ≠
validated factual truth probability
```

Until the individual signals are validated and an appropriate fusion methodology is evaluated, they remain separate outputs.

---

# Tech Stack

## Frontend

```text
React
TypeScript
Vite
Tailwind CSS
Axios
Recharts
Cytoscape.js
Centrifugo realtime subscription
```

## Backend

```text
Python
Django
Django REST Framework
Django ORM
PostgreSQL
Redis
Procrastinate
Centrifugo HTTP API
HTTPX
```

## Machine Learning

```text
PyTorch
PyTorch Geometric
Hugging Face Transformers
BERTurk
NetworkX
scikit-learn
pandas
NumPy
```

## Infrastructure

```text
Docker
Docker Compose
Nginx
GitHub Actions
GitHub Container Registry
```

---

# NLP Pipeline

The NLP implementation is located primarily under:

```text
backend/nlp_engine/
```

The text classifier supports two execution modes.

## BERTurk Inference

If the fine-tuned local model is available under:

```text
backend/ml_models/berturk-mide22/
```

the system loads the Transformer model and performs real inference.

Current text labels are:

```text
gercek
sahte
belirsiz
```

The fine-tuned model is based on:

```text
dbmdz/bert-base-turkish-cased
```

and was trained using the Turkish fake-news dataset used in the project experiments.

The local model checkpoint is intentionally excluded from Git because of its size.

## Heuristic Fallback

If the BERTurk checkpoint is unavailable, the system falls back to a lightweight deterministic heuristic classifier.

This makes it possible to run:

```text
development
CI
basic integration tests
```

without downloading or storing the full Transformer checkpoint.

The fallback classifier is **not intended as a replacement for the trained NLP model**.

---

# GNN Pipeline

The propagation-network analysis is implemented using **PyTorch Geometric**.

The current deployment architecture is:

```text
Model              GCN
Dataset            UPFD / PolitiFact
Input dimensions   14
Hidden dimensions  64
Output classes     2
Pooling            mean + max + add
Classes            fake / real
```

The GNN receives a graph representation derived from a `PropagationGraph`.

---

# GNN Feature Representation

Each node is represented by **14 aligned features**:

```text
8 profile features
+
6 structural features
=
14 features
```

## Profile Features

The aligned profile representation includes:

```text
verified
followers_count
following_count
post_count
listed_count
account_month
name_word_count
description_word_count
```

Count-based values are transformed before being passed to the model.

## Structural Features

Propagation-network structure contributes:

```text
in-degree
out-degree
total degree
root indicator
leaf indicator
propagation depth
```

These features allow the GNN to analyse both user metadata and propagation topology.

---

# GNN Data Flow

```text
PropagationGraph
      │
      ▼
Node metadata
      │
      ├── 8 aligned profile features
      │
      └── 6 structural features
      │
      ▼
14-dimensional node matrix
      │
      ▼
PyTorch Geometric Data
      │
      ▼
GCN layers
      │
      ▼
Graph embeddings
      │
      ▼
mean + max + add pooling
      │
      ▼
Classifier
      │
      ▼
fake / real logits
      │
      ▼
softmax
      │
      ▼
fake_probability
real_probability
predicted_label
confidence
```

---

# GNN Benchmarking

The project includes benchmark code for:

```text
GCN
GAT
GraphSAGE
```

using UPFD / PolitiFact.

Experiments were run across multiple random seeds to avoid selecting a model based on a single lucky run.

The architecture was selected using **validation performance**, not test-set performance.

Current aligned multi-seed results:

| Model | Test Accuracy | Test Macro-F1 |
| --- | ---: | ---: |
| GCN | 0.8000 ± 0.0190 | 0.7994 ± 0.0197 |
| GAT | 0.7756 ± 0.0126 | 0.7751 ± 0.0129 |
| GraphSAGE | 0.7122 ± 0.0171 | 0.7095 ± 0.0172 |

Validation Macro-F1:

```text
GCN        0.8630 ± 0.0140
GAT        0.8503 ± 0.0280
GraphSAGE  0.8487 ± 0.0267
```

The current deployment architecture is therefore **GCN**.

Seed 1 is used for the current local deployment checkpoint because it belongs to the group of runs tied for the highest validation score. Test performance was **not used to break the validation tie**.

---

# Cross-Domain Limitation

The GNN benchmark dataset and deployment domain are different.

```text
Training / benchmark:
UPFD / PolitiFact

Current application domain:
Turkish social-media content / X
```

Therefore:

```text
UPFD benchmark performance
≠
Turkish real-world deployment performance
```

The inference output explicitly includes:

```json
{
  "benchmark_dataset": "UPFD/politifact",
  "cross_domain": true
}
```

This limitation is also shown in the frontend.

---

# NLP and GNN Separation

The NLP and GNN branches are intentionally kept independent.

```text
Text
 └── BERTurk

Propagation graph
 └── GCN
```

BERTurk output is not reused as a training label for the GNN.

This avoids circular evaluation and direct information leakage between the text and graph branches.

A future fusion model may combine both signals only after each branch has been independently validated.

---

# Social Data Ingestion

Social-media integration is implemented under:

```text
backend/external/
```

The X client supports two modes.

## Real X API Mode

If:

```text
X_API_BEARER_TOKEN
```

is configured, the backend uses X API v2.

The current integration retrieves post and user metadata such as:

```text
post id
text
author id
username
name
description
created_at
conversation id
language
interaction counts
followers count
following count
post count
listed count
verified state
```

This metadata is mapped into the propagation-graph representation.

## Mock Fallback

If an X bearer token is not configured, the application uses a deterministic mock client.

This allows the complete pipeline to be tested without requiring paid X API access.

Mock data is intended only for development and demonstration purposes.

---

# Propagation Graph

Propagation graphs are stored in PostgreSQL.

Each graph contains:

```text
nodes
edges
node metadata
propagation relationships
```

The backend converts this representation into a PyTorch Geometric graph before GNN inference.

The frontend visualises propagation networks using **Cytoscape.js**.

Users can inspect nodes interactively in the Analysis Detail interface.

---

# Asynchronous Processing

VERITAS uses **Procrastinate** as the background task queue.

Procrastinate uses PostgreSQL for task persistence.

The main task is:

```text
procrastinate_app.tasks.run_analysis_task
```

Its execution flow is:

```text
Analysis
   │
   ▼
NLP
   │
   ▼
Propagation Graph
   │
   ▼
GNN
   │
   ▼
Bot Analysis
   │
   ▼
Database Save
   │
   ▼
Realtime Completion Event
```

The worker can be started with:

```bash
python manage.py procrastinate worker
```

---

# Realtime Progress

Centrifugo is used for realtime analysis progress events.

The backend publishes through the Centrifugo HTTP API.

Channel format:

```text
analysis:<analysis_id>
```

Example:

```text
analysis:4
```

A progress event can contain:

```json
{
  "analysis_id": 4,
  "stage": "gnn",
  "progress": 0.6
}
```

The frontend subscribes to the corresponding analysis channel and updates the UI without polling the entire pipeline.

An important architectural rule is:

```text
Centrifugo failure
must not
fail the analysis job
```

Realtime publishing errors are handled separately from core analysis execution.

---

# Bot Analysis

The bot-analysis branch is currently **experimental/mock**.

The frontend deliberately displays:

```text
Experimental / Mock
```

instead of presenting the value as a validated bot-risk probability.

The next machine-learning milestone is to replace this module with a real bot-detection pipeline.

---

# Frontend

The VERITAS frontend includes:

```text
Dashboard
Analysis Detail
Login
Propagation Graph
Realtime Progress
Light Theme
Dark Theme
Responsive Layout
```

The design uses a professional warm-light / dark-burgundy visual language.

The Analysis Detail page presents:

```text
analysis metadata
realtime progress timeline
NLP result
GNN result
bot-analysis state
network summary
propagation graph
technical JSON details
```

Model outputs are presented with methodological limitations rather than being represented as absolute truth scores.

---

# Dashboard Data

The dashboard contains both:

```text
live pipeline information
and
demonstration analytics
```

Static metrics and trend datasets that are not currently generated by the real analysis backend are explicitly marked:

```text
Demo
Demo veri
```

This prevents demonstration data from being confused with actual analysis results.

---

# Authentication and Authorization

Authentication uses JWT with HttpOnly cookies.

Current roles:

| Role | Permissions |
| --- | --- |
| `admin` | Full platform access |
| `analyst` | Create and execute analyses |
| `viewer` | Read-only access |

Agent tools also support tool-level permission checks.

---

# Repository Structure

```text
backend/
│
├── accounts/
│   └── authentication and RBAC
│
├── agent/
│   └── AI agent tools
│
├── analyses/
│   └── Analysis model and API
│
├── core/
│   └── Django settings and URLs
│
├── data_processing/
│
├── external/
│   ├── X API client
│   └── external service integrations
│
├── graph_engine/
│   ├── aligned feature pipeline
│   ├── PyG adapter
│   ├── GNN inference
│   ├── propagation graph model
│   ├── models/
│   └── tests/
│
├── ml/
│   ├── training scripts
│   └── evaluation/
│
├── ml_models/
│   └── local checkpoints
│       (ignored by Git)
│
├── nlp_engine/
│   └── BERTurk / heuristic NLP
│
├── procrastinate_app/
│   └── asynchronous analysis jobs
│
├── realtime/
│   └── Centrifugo integration
│
├── requirements.txt
└── requirements-ml.txt


frontend/
│
├── src/
│   ├── api/
│   ├── components/
│   ├── pages/
│   ├── realtime/
│   └── types/
│
├── Dockerfile
└── package.json


infra/
│
├── centrifugo/
│   └── config.json
│
└── nginx.conf


.github/
└── workflows/
    ├── ci.yml
    └── cd.yml


docker-compose.yml
README.md
```

---

# Local Development

## 1. Clone Repository

```bash
git clone https://github.com/ikrabaser/disinfo-detection-platform.git
cd disinfo-detection-platform
```

---

## 2. Start Infrastructure

Start PostgreSQL, Redis and Centrifugo:

```bash
docker compose up -d postgres redis centrifugo
```

Current development ports:

```text
PostgreSQL   5432
Redis        6379
Centrifugo   8002
```

Check:

```bash
docker compose ps
```

---

# Backend Setup

```bash
cd backend

python -m venv .venv
```

Git Bash / Windows:

```bash
source .venv/Scripts/activate
```

PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the complete ML dependency set:

```bash
pip install -r requirements-ml.txt
```

Create environment configuration:

```bash
cp .env.example .env
```

Apply migrations:

```bash
python manage.py migrate
```

Run Django:

```bash
python manage.py runserver 8321 --noreload
```

Development backend:

```text
http://127.0.0.1:8321
```

---

# Background Worker

Run the Procrastinate worker in a separate terminal:

```bash
cd backend
source .venv/Scripts/activate

python manage.py procrastinate worker
```

On Windows, Procrastinate may display:

```text
Skipping signal handling, does not work on Windows
```

This is expected for local development.

---

# Frontend Setup

Open another terminal:

```bash
cd frontend

npm ci
npm run dev
```

The Vite development server typically runs on:

```text
http://localhost:5173
```

or the next available Vite port if `5173` is already occupied.

---

# Centrifugo

The development Centrifugo container is exposed at:

```text
http://localhost:8002
```

Example backend API endpoint:

```text
http://localhost:8002/api
```

Development mode currently uses insecure client/admin configuration for local development.

This configuration must be hardened before production deployment.

---

# Running Tests

## Backend

```bash
cd backend
source .venv/Scripts/activate

pytest -q
```

Current validated suite:

```text
24 passed
```

PyTorch / PyTorch Geometric may emit deprecation warnings during tests. These warnings do not currently fail the suite.

---

# Frontend Production Build

```bash
cd frontend

npm ci
npm run build
```

This performs:

```text
TypeScript build
+
Vite production build
```

---

# Docker Compose Validation

From the repository root:

```bash
docker compose config
```

---

# CI

GitHub Actions CI is configured in:

```text
.github/workflows/ci.yml
```

CI runs on pushes to:

```text
ikra
develop
main
```

and pull requests targeting:

```text
develop
main
```

The CI pipeline includes:

```text
Backend checks
├── PostgreSQL service
├── Redis service
├── Python dependency installation
├── Django system check
├── migration drift check
├── database migrations
└── pytest

Frontend build
├── npm ci
└── TypeScript + Vite production build

Docker Compose validation
└── docker compose config

CI Summary
└── GitHub Actions summary
```

The backend CI environment installs:

```text
requirements-ml.txt
```

so PyTorch and PyTorch Geometric based imports are validated in CI as well.

---

# CD

Continuous Delivery is configured in:

```text
.github/workflows/cd.yml
```

The CD workflow is triggered by a push or merge to:

```text
main
```

It builds and publishes:

```text
Backend Docker image
Frontend Docker image
```

to GitHub Container Registry.

Images receive:

```text
latest
```

and immutable commit SHA tags.

Conceptually:

```text
main
  │
  ▼
GitHub Actions
  │
  ├── Build backend
  │
  └── Build frontend
  │
  ▼
GitHub Container Registry
```

The first validated container-delivery workflow has successfully completed.

---

# ML Model Artifacts

Large trained model checkpoints are intentionally excluded from Git.

Examples:

```text
backend/ml_models/berturk-mide22/

backend/ml_models/upfd_aligned/
```

This keeps the repository lightweight and avoids committing hundreds of megabytes of binary model artifacts.

However, this also means a production deployment needs a separate model-artifact delivery mechanism.

Possible future solutions include:

```text
GitHub Releases
S3-compatible object storage
model registry
private artifact storage
deployment-time model download
```

The current GHCR backend image therefore represents the application environment but requires appropriate model provisioning for full trained-model inference in production.

---

# Branch Strategy

Development follows:

```text
ikra
  │
  ▼
develop
  │
  ▼
main
```

## `ikra`

Active development branch.

New implementation work is developed and validated here.

## `develop`

Integration branch.

Validated changes from `ikra` are merged here through a pull request.

## `main`

Stable release branch.

Validated `develop` changes are promoted to `main`.

A merge to `main` triggers the container-delivery workflow.

Current release workflow:

```text
ikra
  │
  │ Pull Request
  ▼
develop
  │
  │ Pull Request
  ▼
main
  │
  ▼
CI
  │
  ▼
CD
  │
  ▼
GHCR
```

---

# Current CI/CD Status

The current project state has been validated through:

```text
Backend tests             PASS
Django system check       PASS
Migration validation      PASS
Frontend production build PASS
Docker Compose validation PASS
CI workflow               PASS
CD container publication  PASS
```

---

# Security

Current security-related components include:

```text
JWT authentication
HttpOnly cookies
role-based access control
DRF permissions
DRF throttling
tool-level agent permissions
CORS configuration
```

Development secrets and API keys must not be committed to Git.

Production deployment must replace the development Centrifugo configuration with authenticated client subscriptions and hardened channel authorization.

---

# Known Limitations

The current project intentionally documents the following limitations.

## GNN Domain Shift

The deployed GNN was trained on:

```text
UPFD / PolitiFact
```

and is currently applied experimentally to:

```text
Turkish X data
```

Real Turkish graph-labelled evaluation data is still required.

## Model Confidence

Model confidence should not be interpreted as:

```text
probability that a claim is factually true
```

without calibration and domain validation.

## Bot Detection

Bot analysis is currently experimental/mock.

A real bot-detection model has not yet been integrated.

## Truth Score

The application intentionally does not calculate a single aggregate truth score yet.

## Model Deployment

Model checkpoints are excluded from Git and require external artifact provisioning.

## Realtime Security

Centrifugo currently uses development configuration and requires production authentication hardening.

## Dashboard Demo Data

Some aggregate dashboard statistics and historical trend visualisations use explicitly labelled demo data.

## Monitoring

Full Prometheus / Grafana / Sentry observability is not yet complete.

---

# Next Milestones

```text
1. Implement real bot detection
2. Evaluate NLP + GNN + bot signal fusion
3. Build / obtain Turkish labelled propagation-graph data
4. Validate GNN performance on Turkish social-media graphs
5. Add production ML artifact provisioning
6. Harden Centrifugo authentication and channel authorization
7. Complete monitoring and observability
8. Improve production deployment workflow
```

---

# Academic Methodology Notes

VERITAS is designed to preserve separation between experimental evidence and product presentation.

The project therefore follows several methodological principles:

```text
Validation data is used for model selection.

Test data is not used to select the architecture.

BERTurk output is not reused as a GNN training label.

Cross-domain GNN inference is explicitly labelled.

Mock bot-analysis values are explicitly labelled.

Demo dashboard data is explicitly labelled.

Raw confidence is not presented as factual truth probability.

An aggregate truth score is not fabricated before validation.
```

These decisions are intended to make the system technically demonstrable while keeping its research limitations visible.

---

# Project Status

Current implemented state:

```text
Authentication                 ✅
Role-based access              ✅
Django REST API                ✅
PostgreSQL                     ✅
Redis                          ✅
X API integration              ✅ real + mock fallback
BERTurk NLP inference          ✅
Propagation graph pipeline     ✅
PyTorch Geometric              ✅
GCN inference                  ✅
Multi-seed GNN benchmark       ✅
Procrastinate async jobs       ✅
Centrifugo realtime progress   ✅
React realtime integration     ✅
Cytoscape graph UI             ✅
Light / dark theme             ✅
CI                             ✅
Container CD                   ✅

Real bot detection             ⏳
Signal fusion                  ⏳
Turkish graph validation       ⏳
Production model provisioning  ⏳
Production realtime hardening  ⏳
Full observability             ⏳
```

---

# Disclaimer

VERITAS is currently an academic / graduation-project system.

Its model outputs are intended for research, experimentation and decision-support demonstrations.

They should not be interpreted as definitive judgments about the factual truth of real-world claims without appropriate dataset validation, calibration, source verification and human review.
