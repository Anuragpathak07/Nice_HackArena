# NICE HackArena — KYC & AML Onboarding Platform

> **Project Origin:** This repository is a consolidated build. Code was pulled from multiple contributors' repositories, integrated into a unified full-stack project, and pushed to GitHub as a single cohesive codebase.

A full-stack compliance operations platform for **Know Your Customer (KYC)** and **Anti-Money Laundering (AML)** workflows. It enables compliance officers to onboard customers, run deterministic identity verification and watchlist screening, calculate explainable risk ratings, perform continuous impact analysis via a **KYC Impact Radar**, manage alerts and cases, and maintain a regulatory-grade immutable audit trail.

---

## Table of Contents

- [Features](#features)
- [Architecture Overview](#architecture-overview)
- [Frontend Deep Dive](#frontend-deep-dive)
- [Backend Deep Dive](#backend-deep-dive)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Frontend Setup](#frontend-setup)
  - [Backend Setup](#backend-setup)
- [Data Modes](#data-modes)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Key Design Decisions](#key-design-decisions)
- [Documentation](#documentation)
- [License](#license)

---

## Features

### 1. Applicant Onboarding
Full CRUD for customer onboarding with strict state transitions (`PENDING` → `APPROVED` / `REJECTED` / `REVIEW_REQUIRED`). Each new applicant is automatically screened against the active watchlist upon creation. Officers can manually verify or reject applicants, with every action logged to the immutable audit trail.

### 2. Identity Consistency Engine
Field-by-field structured comparisons between applicant data and ID records — Name, DOB, Address, and country-specific ID formats — with per-field match statuses and human-readable evidence. The consistency check produces a pass/fail result with a detailed explanation for the compliance officer.

### 3. Watchlist Screening & Risk Rating
Multi-stage deterministic matching using Exact, Normalized, and RapidFuzz (token sort / ratio / partial) algorithms. Every match produces a structured evidence matrix (`NAME_SIMILARITY`, `DOB_MATCH`, `COUNTRY_MATCH`, `ADDRESS_SIMILARITY`) and a configurable risk level (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). The risk engine also generates a recommended action (`NO_ACTION`, `MANUAL_REVIEW`, `ENHANCED_REVIEW`).

### 4. Compliance Dashboard
Server-side aggregated metrics: applicant status breakdown, risk distribution, active alerts, open cases, and recent audit activity. The dashboard is the landing page and provides at-a-glance operational awareness.

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

The pipeline is **idempotent** — re-running analysis on the same watchlist event returns the existing completed analysis without generating duplicate alerts or cases.

### 6. Alerts & Case Management
Compliance alerts are auto-generated from screening results and impact analyses. Officers can escalate alerts to cases, assign them to team members, and resolve them with a final disposition (`APPROVED`, `REJECTED`, `DISMISSED`). Resolving a case also updates the applicant's status and resolves the linked alert.

### 7. Immutable Audit Trail
Append-only audit logging captures previous state, new state, actor, timestamp, and justification for every compliance-relevant action — applicant creation, status changes, screening matches, watchlist edits, impact analysis, alert resolutions, and case resolutions.

### 8. AI Copilot (Optional)
An optional Groq-powered (`llama-3.3-70b-versatile`) executive summary generator that synthesizes applicant data, screening results, and consistency checks into a 2-paragraph narrative for compliance officers. Fully isolated behind a service interface with a deterministic fallback — core compliance workflows never depend on external AI availability.

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

## Frontend Deep Dive

The frontend is a **TanStack Start** application (SSR-capable React framework built on Vite) located at `frontend/compliance-guardian/`. It provides a dark-first, compliance-operations workspace with seven file-based routes.

### Routing & Pages

TanStack Start uses **file-based routing** — every `.tsx` file in `src/routes/` defines a URL route. There is no `pages/` directory or manual route configuration.

| File | URL | Purpose |
|---|---|---|
| `src/routes/index.tsx` | `/` | **Compliance Dashboard** — aggregated metrics, risk distribution chart, recent activity feed |
| `src/routes/applicants.tsx` | `/applicants` | **Applicant Directory** — searchable/filterable table of all applicants with status and risk badges |
| `src/routes/applicants_.$id.tsx` | `/applicants/:id` | **Applicant Deep-Dive** — full profile, ID consistency check results, screening history, AI Copilot summary, verify/reject actions |
| `src/routes/impact-radar.tsx` | `/impact-radar` | **KYC Impact Radar** — trigger watchlist re-screening, view before/after state diffs, review affected customers |
| `src/routes/alerts.tsx` | `/alerts` | **Alerts & Cases** — list of compliance alerts with priority/status filters, resolve actions |
| `src/routes/watchlist.tsx` | `/watchlist` | **Watchlist Management** — view and add watchlist entries; adding an entry triggers the Impact Radar |
| `src/routes/audit-logs.tsx` | `/audit-logs` | **Audit Trail** — immutable, append-only log of all compliance actions |
| `src/routes/__root.tsx` | *(shell)* | **App Shell** — wraps every page with sidebar navigation, header, QueryClientProvider, and toast notifications |

### UI Component Library

Built on **shadcn/ui** (Radix UI primitives + Tailwind CSS v4) with 40+ reusable components:

- **Layout:** `app-shell`, `sidebar`, `page`, `theme-provider`
- **Data Display:** `table`, `card`, `tabs`, `chart` (Recharts), `avatar`, `badge`
- **Forms:** `input`, `select`, `checkbox`, `switch`, `radio-group`, `slider`, `textarea`, `form`, `input-otp`
- **Overlays:** `dialog`, `sheet`, `drawer`, `popover`, `hover-card`, `tooltip`, `command`, `context-menu`, `dropdown-menu`, `menubar`, `navigation-menu`
- **Feedback:** `alert`, `sonner` (toast), `skeleton`, `progress`
- **Navigation:** `breadcrumb`, `pagination`, `collapsible`, `resizable`, `scroll-area`, `separator`, `toggle`, `toggle-group`, `aspect-ratio`, `calendar`, `carousel`

### Design System

All visual colors are defined as **semantic OKLCH tokens** in `src/styles.css`:

- **Dark-first** — the app boots in dark mode (`<html className="dark">`)
- **Dual theme** — complete light and dark palettes via `:root` and `.dark` CSS custom properties
- **Semantic naming** — `--color-primary`, `--color-success`, `--color-warning`, `--color-risk`, `--color-destructive`, `--color-chart-1` through `--color-chart-5`
- **Custom utilities** — `glass-panel` (backdrop-blur card), `filter-select` (styled dropdown), `data-table`, `detail-list`, `check-pass`/`check-fail`, `action-badge`, `risk-dot-0` through `risk-dot-3`, `radar-scan` (animated radar pulse)
- **Typography** — Plus Jakarta Sans font family
- **Accessibility** — `prefers-reduced-motion` media query disables all animations

### Data Layer

**Unified API Client** (`src/services/api.ts`):
- Single `api` object with methods for every backend endpoint
- Automatic error formatting from FastAPI's `detail` response
- Graceful fallbacks — if the backend is unreachable, the dashboard, audit logs, and impact radar load sensible fallback data so the UI is never broken
- Status code mapping: `REVIEW_REQUIRED` → `REVIEW`, `APPROVED` → `VERIFIED`

**TanStack Query Hooks** (`src/hooks/use-compliance.ts`):
- `useDashboard()`, `useApplicants()`, `useApplicant(id)`, `useWatchlist()`, `useAlerts()`, `useAuditLogs()` — suspense-based queries with staleTime caching
- `useComplianceMutations()` — `createApplicant`, `addWatchlist`, `runImpact`, `reviewImpact`, `resolveAlert`, `explainApplicant`, `verifyApplicant`, `rejectApplicant`
- **Cross-page invalidation** — every mutation invalidates all relevant query keys (`dashboard`, `applicants`, `watchlist`, `alerts`, `audit-logs`) so data stays consistent across pages

### State Management

- **Server state** — TanStack Query (caching, invalidation, suspense)
- **UI state** — React hooks (`useState`, `useEffect`)
- **Theme** — CSS custom properties toggled via `.dark` class on `<html>`
- **No global store** — the app is server-state-driven; no Redux/Zustand needed

### Frontend Configuration

| Env Var | Purpose |
|---|---|
| `VITE_API_URL` / `NEXT_PUBLIC_API_URL` | Backend API base URL (default: `http://localhost:8000/api`) |
| `VITE_USE_MOCK` / `NEXT_PUBLIC_USE_MOCK` | Toggle mock data mode (default: `false`) |

---

## Backend Deep Dive

The backend is a **FastAPI** modular monolith located at `backend/`. It follows a clean layered architecture: **API → Services → Repositories → Models**, with a deterministic matching/risk engine at its core.

### Application Entrypoint (`app/main.py`)

- Creates all 10 database tables on startup via `Base.metadata.create_all(bind=engine)`
- Configures CORS (allow all origins for frontend integration)
- Mounts 7 API routers under `/api/v1`
- Health check endpoint at `GET /` and `GET /health`

### Core Infrastructure

| Module | Purpose |
|---|---|
| `app/core/config.py` | Pydantic `BaseSettings` — loads `.env`, defines `DATABASE_URL`, `FUZZY_HIGH_THRESHOLD` (90.0), `FUZZY_MEDIUM_THRESHOLD` (75.0) |
| `app/core/database.py` | SQLAlchemy engine with `pool_pre_ping`, `SessionLocal` session factory, `get_db` dependency |
| `app/core/security.py` | Auth & tenant isolation headers (placeholder for production) |

### API Layer (`app/api/v1/`)

Seven routers, each mapping to a domain:

| Router | Prefix | Endpoints |
|---|---|---|
| `applicants_router` | `/applicants` | CRUD, verify, reject, consistency-check, screen, screening-results, explain |
| `watchlist_router` | `/watchlist` | List, create (triggers Impact Radar), get, update (triggers Impact Radar) |
| `impact_router` | `/watchlist/{id}/impact-analysis`, `/impact-analysis/{id}` | Trigger analysis, get analysis detail with before/after results |
| `alerts_router` | `/alerts` | List (filter by status/priority), get, resolve |
| `cases_router` | `/cases` | List, create from alert, get, resolve |
| `dashboard_router` | `/dashboard/summary` | Aggregated metrics |
| `audit_router` | `/audit-logs` | List (filter by applicant, paginated) |

Every mutating endpoint writes an `AuditLog` entry within the same request.

### Service Layer (`app/services/`)

| Service | Responsibility |
|---|---|
| `ScreeningService` | Screens an applicant against all active watchlist entries. For each match above the medium threshold, creates a `ScreeningResult` + `ScreeningEvidence` records, a `ComplianceAlert`, and updates the applicant's risk level and status. Logs audit events for both match and clear outcomes. |
| `ImpactService` | Executes the **9-stage KYC Impact Radar pipeline**. Checks idempotency (returns existing analysis if already completed for the same watchlist + event). Iterates all applicants, runs matching, recalculates risk, preserves before/after state in `ImpactResult`, updates applicant status, generates alerts, and logs audit events. |
| `RiskEngineService` | Pure deterministic function: `(match_score, match_type, country_match, consistency_passed) → (risk_level, recommended_action)`. Uses configurable thresholds. |
| `MatchingService` | Wraps RapidFuzz (`token_sort_ratio`, `ratio`, `partial_ratio`). Normalizes names (lowercase, strip punctuation, remove honorifics). Classifies match type: `EXACT`, `NORMALIZED`, `FUZZY_HIGH`, `FUZZY_MEDIUM`, `NO_MATCH`. Produces structured evidence signals: `NAME_SIMILARITY`, `COUNTRY_MATCH`, `DOB_MATCH`. |
| `ConsistencyService` | Compares applicant fields against ID record fields (name, DOB, address). Returns pass/fail with per-field match details and a human-readable explanation. |
| `CaseService` | Creates cases from alerts (inherits priority and recommended action). Resolves cases with final disposition, updates applicant status, resolves linked alert, logs audit. |
| `ReScreeningService` | Re-screens all active applicants against a specific watchlist entry (used by the watchlist router's `/rescreen` endpoint). |
| `LLMService` | Generates executive case summaries via Groq (`llama-3.3-70b-versatile`). If the API key is missing or the call fails, falls back to a deterministic template-based summary. |

### Repository Layer (`app/repositories/`)

Data access objects providing raw database operations only — no business logic. One repository per entity:

`ApplicantRepository`, `IDRecordRepository`, `WatchlistRepository`, `ScreeningRepository`, `ImpactRepository`, `AlertRepository`, `CaseRepository`, `AuditRepository`

### Matching & Risk Engine (`app/matching/`)

The deterministic core of the platform:

```
Input: Applicant (name, dob, address, country) + Watchlist Entry (name, country, reason)
                    │
                    ▼
        ┌───────────────────────┐
        │   Name Normalization  │  lowercase, strip punctuation, remove titles
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   RapidFuzz Scoring   │  token_sort_ratio, ratio, partial_ratio
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Match Classification │  EXACT / NORMALIZED / FUZZY_HIGH / FUZZY_MEDIUM / NO_MATCH
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Evidence Matrix      │  NAME_SIMILARITY, COUNTRY_MATCH, DOB_MATCH
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Risk Engine          │  score + match_type + country_match → risk_level + action
        └───────────────────────┘
```

**Risk Matrix:**

| Match Score | Match Type | Country Match | Risk Level | Recommended Action |
|---|---|---|---|---|
| >= 90% or EXACT/NORMALIZED | Any | Yes | **CRITICAL** | ENHANCED_REVIEW |
| >= 90% or EXACT/NORMALIZED | Any | No | **HIGH** | ENHANCED_REVIEW |
| >= 75% | FUZZY_HIGH | Yes | **HIGH** | ENHANCED_REVIEW |
| >= 75% | FUZZY_HIGH | No | **MEDIUM** | MANUAL_REVIEW |
| < 75% | NO_MATCH | — | **LOW** | NO_ACTION |

### Database Layer

**10-table relational schema** on Supabase PostgreSQL (with SQLite fallback for local development):

| Table | Purpose |
|---|---|
| `applicants` | Customer profiles with status and risk level |
| `id_records` | ID document data for consistency checks |
| `watchlist` | Watchlist/PEP/sanctions entries with version tracking |
| `screening_results` | Each applicant-vs-watchlist match with score and risk |
| `screening_evidence` | Structured evidence signals per screening result |
| `impact_analyses` | Master record for each impact radar execution |
| `impact_results` | Before/after state diffs for each affected applicant |
| `compliance_alerts` | Auto-generated alerts from screening and impact radar |
| `compliance_cases` | Escalated cases with assignment and resolution |
| `audit_logs` | Append-only immutable audit trail |

**Indexes:** `applicants(status, risk_level)`, `watchlist(normalized_name)`, `screening_results(application_id)`, `impact_results(analysis_id)`, `compliance_alerts(application_id, status)`, `compliance_cases(status)`, `audit_logs(application_id)`

### Backend Configuration

| Env Var | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `sqlite:///./kyc_aml.db` |
| `GROQ_API_KEY` | Groq API key for AI Copilot | *(none — fallback mode)* |
| `FUZZY_HIGH_THRESHOLD` | High confidence match cutoff | `90.0` |
| `FUZZY_MEDIUM_THRESHOLD` | Medium confidence match cutoff | `75.0` |

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
│   │   ├── main.py                     # FastAPI entrypoint, CORS, router mounting
│   │   ├── core/
│   │   │   ├── config.py               # Settings (thresholds, DB URL, env)
│   │   │   ├── database.py             # SQLAlchemy engine, session, Base
│   │   │   └── security.py             # Auth & tenant isolation
│   │   ├── api/v1/
│   │   │   ├── compliance.py           # All 7 routers (applicants, watchlist,
│   │   │   │                           #   impact, alerts, cases, dashboard, audit)
│   │   │   ├── applicants.py           # Standalone applicant router (alternate)
│   │   │   └── watchlist.py            # Standalone watchlist router (alternate)
│   │   ├── models/                     # SQLAlchemy ORM models (10 tables)
│   │   ├── schemas/                    # Pydantic request/response schemas
│   │   ├── repositories/               # Data access layer (8 repositories)
│   │   ├── services/                   # Business logic (8 services)
│   │   │   ├── screening_service.py
│   │   │   ├── impact_service.py       # KYC Impact Radar 9-stage pipeline
│   │   │   ├── risk_service.py         # Deterministic risk matrix
│   │   │   ├── matching_service.py     # RapidFuzz wrapper + evidence
│   │   │   ├── consistency_service.py
│   │   │   ├── case_service.py
│   │   │   ├── rescreening_service.py
│   │   │   └── llm_service.py          # Groq AI copilot + fallback
│   │   └── matching/                   # Deterministic matching utilities
│   ├── tests/
│   │   └── test_compliance_engine.py   # 20 integration tests
│   ├── seed_data.py                    # Synthetic dataset ingestion
│   └── kyc_aml.db                      # SQLite fallback database
│
├── frontend/
│   └── compliance-guardian/
│       ├── src/
│       │   ├── routes/                 # File-based routes (7 pages + root shell)
│       │   │   ├── __root.tsx          # App shell (sidebar, header, outlet)
│       │   │   ├── index.tsx           # Dashboard
│       │   │   ├── applicants.tsx      # Applicant directory
│       │   │   ├── applicants_.$id.tsx # Applicant deep-dive
│       │   │   ├── impact-radar.tsx    # KYC Impact Radar
│       │   │   ├── alerts.tsx          # Alerts & cases
│       │   │   ├── watchlist.tsx       # Watchlist management
│       │   │   └── audit-logs.tsx      # Audit trail
│       │   ├── components/
│       │   │   ├── app/                # app-shell, page, theme-provider
│       │   │   └── ui/                 # 40+ shadcn/ui components
│       │   ├── hooks/
│       │   │   ├── use-compliance.ts   # TanStack Query hooks + mutations
│       │   │   └── use-mobile.tsx
│       │   ├── services/
│       │   │   └── api.ts              # Unified API client (mock/live)
│       │   ├── lib/
│       │   │   ├── config.ts           # API_BASE_URL, USE_MOCK_DATA
│       │   │   ├── mock-data.ts        # Comprehensive mock dataset
│       │   │   ├── utils.ts            # Utility functions
│       │   │   ├── error-page.ts
│       │   │   ├── error-capture.ts
│       │   │   └── lovable-error-reporting.ts
│       │   ├── types/index.ts          # TypeScript type definitions
│       │   ├── constants/navigation.ts
│       │   ├── styles.css              # OKLCH design tokens + custom utilities
│       │   ├── router.tsx
│       │   ├── server.ts
│       │   └── start.ts
│       ├── public/robots.txt
│       ├── package.json
│       ├── vite.config.ts
│       ├── tsconfig.json
│       └── components.json             # shadcn/ui config
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
# Edit .env.local:
#   VITE_API_URL=http://localhost:8000/api
#   VITE_USE_MOCK=false

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
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic-settings rapidfuzz groq python-dotenv

# Configure environment
cp .env.example .env
# Edit .env:
#   DATABASE_URL=postgresql://user:pass@host:5432/kyc_aml
#   GROQ_API_KEY=your_key_here          (optional)

# Seed synthetic data (optional — loads 100 applicants, 97 ID records, 30 watchlist entries)
python seed_data.py

# Start API server (http://localhost:8000)
uvicorn app.main:app --reload

# Interactive API docs:
#   http://localhost:8000/docs     (Swagger UI)
#   http://localhost:8000/redoc    (ReDoc)
```

---

## Data Modes

The frontend supports two data modes:

### Mock Mode
Uses comprehensive in-memory mock data — no backend required. The `USE_MOCK_DATA` flag in `src/lib/config.ts` controls this. The API client also has built-in fallback data for the dashboard, audit logs, and impact radar if the backend is unreachable.

```env
VITE_USE_MOCK=true
```

### Live Backend Mode
Connects to the FastAPI backend for real database operations.

```env
VITE_API_URL=http://localhost:8000/api
VITE_USE_MOCK=false
```

> Both `NEXT_PUBLIC_` and `VITE_` env var forms are accepted (TanStack Start runs on Vite).

---

## API Reference

All endpoints are prefixed with `/api`. Interactive documentation is auto-generated at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### Applicants

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/applicants` | List applicants (paginated: `skip`, `limit`, `status`, `risk_level`) |
| `POST` | `/api/applicants` | Create applicant & auto-run initial screening |
| `GET` | `/api/applicants/{id}` | Get applicant with compliance status |
| `PUT` | `/api/applicants/{id}` | Update applicant profile |
| `POST` | `/api/applicants/{id}/verify` | Mark applicant as verified/approved |
| `POST` | `/api/applicants/{id}/reject` | Reject applicant |
| `POST` | `/api/applicants/{id}/consistency-check` | Field-by-field ID consistency validation |
| `POST` | `/api/applicants/{id}/screen` | Run/re-run watchlist screening |
| `GET` | `/api/applicants/{id}/screening-results` | Full screening history with evidence |
| `POST` | `/api/applicants/{id}/explain` | AI Copilot executive risk report |

### Watchlist

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/watchlist` | List watchlist entries (paginated) |
| `POST` | `/api/watchlist` | Create entry (triggers Impact Radar) |
| `GET` | `/api/watchlist/{id}` | Get watchlist entry details |
| `PUT` | `/api/watchlist/{id}` | Update entry (triggers Impact Radar) |
| `POST` | `/api/watchlist/{id}/rescreen` | Manually re-screen all applicants against this entry |

### KYC Impact Radar

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/watchlist/{id}/impact-analysis` | Manually trigger impact analysis |
| `GET` | `/api/impact-analysis/{id}` | Impact analysis summary + before/after results |

### Alerts & Cases

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/alerts` | List alerts (filter by `status`, `priority`) |
| `GET` | `/api/alerts/{id}` | Alert details |
| `POST` | `/api/alerts/{id}/resolve` | Resolve alert (approve/reject applicant) |
| `GET` | `/api/cases` | List cases (filter by `status`) |
| `POST` | `/api/cases` | Create case from alert |
| `GET` | `/api/cases/{id}` | Case details |
| `POST` | `/api/cases/{id}/resolve` | Resolve case (APPROVED/REJECTED/DISMISSED) |

### Dashboard & Audit

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/summary` | Aggregated dashboard metrics |
| `GET` | `/api/audit-logs` | Immutable audit trail (filter by `application_id`, paginated) |

---

## Database Schema

```sql
-- Core entities
applicants (application_id PK, full_name, dob, address, id_number, occupation, annual_income, country, status, risk_level)
id_records (id_record_id PK, application_id FK, name_on_id, dob_on_id, address_on_id)
watchlist (watchlist_id PK, name, normalized_name, country, reason, status, version)

-- Screening & evidence
screening_results (screening_id PK, application_id FK, watchlist_id FK, match_score, match_type, risk_level, reason, review_status)
screening_evidence (evidence_id PK, screening_id FK, signal, score_value, is_boolean_match, description)

-- KYC Impact Radar
impact_analyses (analysis_id PK, watchlist_id FK, event_type, customers_scanned, potential_matches, high_confidence_matches, review_required, analysis_status)
impact_results (impact_result_id PK, analysis_id FK, application_id FK, screening_id FK, before/after risk_level, watchlist_status, status, risk_change, match_score, recommended_action, reason)

-- Operations
compliance_alerts (alert_id PK, application_id FK, screening_id FK, analysis_id FK, alert_type, priority, title, description, risk_level, match_score, recommended_action, status, resolved_at, resolved_by, resolution_reason)
compliance_cases (case_id PK, application_id FK, alert_id FK, priority, recommended_action, final_action, status, assigned_to, resolved_at, resolution_reason)
audit_logs (audit_id PK, application_id FK, action, entity_type, entity_id, old_value, new_value, performed_by, timestamp, reason)
```

---

## Testing

### Backend Tests

```sh
cd backend

# Install test dependencies
pip install pytest httpx

# Run the compliance engine test suite
pytest tests/test_compliance_engine.py -v
```

The test suite covers **20 scenarios** including:
- Applicant CRUD and state transitions
- Identity consistency checks
- Watchlist screening and risk rating
- KYC Impact Radar pipeline execution
- Alert and case management
- Audit trail integrity

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
| **TanStack Start (SSR)** | File-based routing, server-side rendering, type-safe navigation |
| **OKLCH design tokens** | Perceptually uniform colors, dark-first, complete light/dark themes |

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
