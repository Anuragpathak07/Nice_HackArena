# NICE HackArena — KYC & AML Onboarding Platform

A full-stack compliance operations platform for **Know Your Customer (KYC)** and **Anti-Money Laundering (AML)** workflows. It enables compliance officers to onboard customers, run deterministic identity verification and watchlist screening, calculate explainable risk ratings, perform continuous impact analysis via a **KYC Impact Radar**, manage alerts and cases, and maintain a regulatory-grade immutable audit trail.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Frontend Setup](#frontend-setup)
  - [Backend Setup](#backend-setup)
- [Data Modes](#data-modes)
- [API Reference](#api-reference)
- [Testing](#testing)
- [Key Design Decisions](#key-design-decisions)
- [Documentation](#documentation)
- [License](#license)

---

## Features

### 1. Applicant Onboarding
Full CRUD for customer onboarding with strict state transitions (`PENDING` → `APPROVED` / `REJECTED` / `REVIEW_REQUIRED`). Each new applicant is automatically screened against the active watchlist.

### 2. Identity Consistency Engine
Field-by-field structured comparisons between applicant data and ID records — Name, DOB, Address, and country-specific ID formats — with match statuses and human-readable evidence for every field.

### 3. Watchlist Screening & Risk Rating
Multi-stage deterministic matching using Exact, Normalized, and RapidFuzz (token sort / ratio / partial) algorithms. Every match produces a structured evidence matrix (`NAME_SIMILARITY`, `DOB_MATCH`, `COUNTRY_MATCH`, `ADDRESS_SIMILARITY`) and a configurable risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).

### 4. Compliance Dashboard
Server-side aggregated metrics: applicant status breakdown, risk distribution, active alerts, open cases, and recent audit activity.

### 5. KYC Impact Radar (Core Differentiator)
When a watchlist entry is added or updated, the system executes a **9-stage idempotent pipeline**:

```
Watchlist Event → Analysis Trigger → Candidate Pre-filtering →
Deterministic Matching → Evidence Construction → Risk Recalculation →
Before/After State Diff → Recommended Action → Alert/Case Generation → Audit Log
```

Every impact analysis answers three questions for the compliance officer:
- **WHAT changed?** (e.g., Watchlist Entry W001 "Rajesh Kumar" added for Fraud)
- **WHO is affected?** (e.g., Customer C042 "Rajesh Kummar")
- **WHAT should I do?** (e.g., ENHANCED_REVIEW — 97% name similarity, DOB & country match)

### 6. Alerts & Case Management
Compliance alerts are auto-generated from screening results and impact analyses. Officers can escalate alerts to cases, assign them, and resolve them with a final disposition (`APPROVED`, `REJECTED`, `DISMISSED`).

### 7. Immutable Audit Trail
Append-only audit logging captures previous state, new state, actor, timestamp, and justification for every compliance-relevant action.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (TanStack Start)                │
│  React 19 + Vite + Tailwind CSS v4 + shadcn/ui + Recharts   │
│  File-based routing · TanStack Query · Mock / Live API      │
└──────────────────────────┬──────────────────────────────────┘
                           │  REST / JSON
┌──────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  Modular Monolith · Pydantic v2 · SQLAlchemy · psycopg2     │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌───────────────┐ │
│  │  Applicant│ │ Watchlist│ │  Impact   │ │ Alert / Case  │ │
│  │  Service  │ │ Service  │ │  Service  │ │   Service     │ │
│  └─────┬─────┘ └─────┬────┘ └─────┬─────┘ └──────┬────────┘ │
│        │             │            │               │          │
│  ┌─────▼─────────────▼────────────▼───────────────▼────────┐ │
│  │              Matching & Risk Engine                      │ │
│  │  Normalizer · RapidFuzz · Evidence Matrix · Risk Matrix  │ │
│  └─────────────────────────┬────────────────────────────────┘ │
│                            │                                  │
│  ┌─────────────────────────▼────────────────────────────────┐ │
│  │           Groq AI Copilot (Optional LLM)                 │ │
│  │     Executive risk reports · llama-3.3-70b-versatile     │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              Supabase PostgreSQL (10-Table Schema)           │
│  applicants · id_records · watchlist · screening_results    │
│  screening_evidence · impact_analyses · impact_results      │
│  compliance_alerts · compliance_cases · audit_logs           │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend Framework** | React 19, TanStack Start (Vite), TypeScript |
| **UI Components** | shadcn/ui (Radix UI), Tailwind CSS v4, Lucide icons |
| **Charts** | Recharts |
| **Data Fetching** | TanStack Query v5 |
| **Routing** | TanStack Router (file-based) |
| **Backend Framework** | FastAPI (Python 3.12+) |
| **ORM** | SQLAlchemy |
| **Validation** | Pydantic v2 |
| **Database** | Supabase PostgreSQL (`psycopg2-binary`) |
| **Matching Engine** | RapidFuzz (C++ Levenshtein / Token Sort) |
| **AI Copilot** | Groq API (`llama-3.3-70b-versatile`) — optional |
| **Package Manager** | Bun (frontend), pip/uv (backend) |

---

## Project Structure

```
HackArena/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entrypoint, middleware, CORS
│   │   ├── core/
│   │   │   ├── config.py               # Settings (thresholds, DB URLs, secrets)
│   │   │   ├── database.py             # SQLAlchemy engine & session
│   │   │   └── security.py             # Auth & tenant isolation
│   │   ├── api/v1/                     # REST endpoint modules
│   │   │   ├── applicants.py
│   │   │   ├── watchlist.py
│   │   │   ├── compliance.py           # Screening, consistency, alerts, cases
│   │   │   └── ...
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   ├── schemas/                    # Pydantic request/response schemas
│   │   ├── repositories/               # Data access layer
│   │   ├── services/                   # Business logic
│   │   │   ├── screening_service.py
│   │   │   ├── risk_service.py
│   │   │   ├── impact_service.py       # KYC Impact Radar engine
│   │   │   ├── consistency_service.py
│   │   │   ├── case_service.py
│   │   │   ├── rescreening_service.py
│   │   │   ├── matching_service.py
│   │   │   └── llm_service.py          # Groq AI copilot
│   │   └── matching/                   # Deterministic matching utilities
│   ├── tests/
│   │   └── test_compliance_engine.py   # 20 integration tests
│   ├── seed_data.py                    # Synthetic dataset ingestion
│   └── kyc_aml.db                      # SQLite fallback database
│
├── frontend/
│   └── compliance-guardian/
│       ├── src/
│       │   ├── routes/                 # File-based routes
│       │   │   ├── index.tsx           # Dashboard
│       │   │   ├── applicants.tsx      # Applicant directory
│       │   │   ├── applicants_.$id.tsx # Applicant deep-dive
│       │   │   ├── impact-radar.tsx    # KYC Impact Radar
│       │   │   ├── alerts.tsx          # Alerts & cases
│       │   │   ├── watchlist.tsx       # Watchlist management
│       │   │   └── audit-logs.tsx      # Audit trail
│       │   ├── components/             # shadcn/ui + app components
│       │   ├── hooks/                  # TanStack Query hooks
│       │   ├── services/api.ts         # Unified API client (mock/live)
│       │   ├── lib/                    # Utils, mock data, config
│       │   └── styles.css              # OKLCH design tokens
│       ├── package.json
│       └── vite.config.ts
│
├── package.json                        # Root-level Supabase deps
├── ARCHITECTURE.md                     # Full architecture specification
├── HACKARENA_DECISION_LOG.md           # Design decision record
├── applicants.csv                      # Seed: 100 customer records
├── id_records.csv                      # Seed: 97 ID records
├── watchlist.csv                       # Seed: 30 watchlist/PEP records
└── README.md                           # This file
```

---

## Getting Started

### Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| **Bun** | 1.x+ | Frontend package manager & runtime |
| **Python** | 3.12+ | Backend runtime |
| **PostgreSQL** | 15+ | Primary database (or Supabase account) |
| **pip** or **uv** | Latest | Python package management |

---

### Frontend Setup

```sh
cd frontend/compliance-guardian

# Install dependencies
bun install

# Configure environment
cp .env.example .env.local

# Start dev server (http://localhost:8080)
bun run dev

# Build for production
bun run build

# Lint
bun run lint
```

See [frontend/compliance-guardian/README.md](frontend/compliance-guardian/README.md) for more details.

---

### Backend Setup

```sh
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic-settings rapidfuzz groq

# Configure environment
cp .env.example .env
# Edit .env and set:
#   DATABASE_URL=postgresql://user:pass@host:5432/kyc_aml
#   GROQ_API_KEY=your_key_here          (optional)

# Run database migrations / create tables
# (SQLAlchemy models auto-create on first run, or use Alembic)

# Seed synthetic data (optional)
python seed_data.py

# Start API server (http://localhost:8000)
uvicorn app.main:app --reload

# Interactive API docs available at:
#   http://localhost:8000/docs     (Swagger UI)
#   http://localhost:8000/redoc    (ReDoc)
```

---

## Data Modes

The frontend supports two data modes:

### Mock Mode (default)
Uses comprehensive in-memory mock data — no backend required.

```env
NEXT_PUBLIC_USE_MOCK=true
```

### Live Backend Mode
Connects to the FastAPI backend for real database operations.

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_USE_MOCK=false
VITE_API_URL=http://localhost:8000/api
VITE_USE_MOCK=false
```

> Both `NEXT_PUBLIC_` and `VITE_` env var forms are accepted (TanStack Start runs on Vite).

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| **Applicants** | | |
| `GET` | `/api/applicants` | List applicants (paginated, filter by status/risk) |
| `POST` | `/api/applicants` | Create applicant & run initial screening |
| `GET` | `/api/applicants/{id}` | Get applicant with compliance status |
| `PUT` | `/api/applicants/{id}` | Update applicant profile |
| `POST` | `/api/applicants/{id}/consistency-check` | Field-by-field ID consistency validation |
| `POST` | `/api/applicants/{id}/screen` | Run/re-run watchlist screening |
| `GET` | `/api/applicants/{id}/screening-results` | Full screening history with evidence |
| **Watchlist** | | |
| `GET` | `/api/watchlist` | List watchlist entries |
| `POST` | `/api/watchlist` | Create entry (triggers Impact Radar) |
| `GET` | `/api/watchlist/{id}` | Get watchlist entry details |
| `PUT` | `/api/watchlist/{id}` | Update entry (triggers Impact Radar) |
| **KYC Impact Radar** | | |
| `POST` | `/api/watchlist/{id}/impact-analysis` | Manually trigger impact analysis |
| `GET` | `/api/impact-analysis/{id}` | Impact analysis summary metrics |
| `GET` | `/api/impact-analysis/{id}/results` | Affected customers with before/after diffs |
| **Alerts & Cases** | | |
| `GET` | `/api/alerts` | List compliance alerts |
| `GET` | `/api/alerts/{id}` | Alert details |
| `POST` | `/api/alerts/{id}/resolve` | Resolve alert |
| `GET` | `/api/cases` | List compliance cases |
| `POST` | `/api/cases` | Create case from alert |
| `GET` | `/api/cases/{id}` | Case details |
| `POST` | `/api/cases/{id}/resolve` | Resolve case |
| **Dashboard & Audit** | | |
| `GET` | `/api/dashboard/summary` | Aggregated dashboard metrics |
| `GET` | `/api/audit-logs` | Immutable audit trail |
| `POST` | `/api/applicants/{id}/explain` | Optional AI Copilot risk report |

Interactive API documentation is auto-generated by FastAPI at `/docs` (Swagger UI) and `/redoc` (ReDoc).

---

## Testing

### Backend Tests

```sh
cd backend

# Run all tests (requires pytest)
pip install pytest httpx

# Run the compliance engine test suite
pytest tests/test_compliance_engine.py -v
```

The test suite covers 20 scenarios including onboarding, screening, consistency checks, impact radar, case management, and audit logging.

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **FastAPI** for backend | Native async, auto OpenAPI docs, Pydantic v2 validation, high throughput |
| **Supabase PostgreSQL** | ACID compliance, enterprise-grade, PII-safe, production-ready |
| **10-table relational schema** | Full explainability with before/after state diffs and structured evidence matrices |
| **RapidFuzz + structured evidence** | 100% deterministic, explainable matching — no black-box ML |
| **Groq for optional AI copilot** | Ultra-fast LPU inference; isolated behind service interface with deterministic fallback |
| **KYC Impact Radar pipeline** | Idempotent 9-stage analysis answering WHAT / WHO / WHAT action |
| **Modular monolith** | Simple deployment at MVP scale; seams exist for future microservices |
| **Mock-first frontend** | Full UI development without backend dependency; seamless live toggle |

See [HACKARENA_DECISION_LOG.md](HACKARENA_DECISION_LOG.md) for full decision records with alternatives and trade-offs.

---

## Documentation

| Document | Description |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Complete architecture spec: domain model, schema, data flow, API contract, scalability plan |
| [HACKARENA_DECISION_LOG.md](HACKARENA_DECISION_LOG.md) | Design decision records with alternatives and trade-offs |
| [frontend/compliance-guardian/README.md](frontend/compliance-guardian/README.md) | Frontend setup, data modes, route reference |
| [frontend/compliance-guardian/roadmap.md](frontend/compliance-guardian/roadmap.md) | Frontend development roadmap |
| [frontend/compliance-guardian/src/routes/README.md](frontend/compliance-guardian/src/routes/README.md) | Routing conventions |

---

## License

Internal project — All rights reserved.
