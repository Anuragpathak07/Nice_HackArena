# HACKARENA DECISION LOG

## Frontend implementation — 28 September 2026

- Added **Clear**, a white, minimal React + TypeScript + Vite interface using the existing FastAPI backend. The generic Next.js Markdown templates are reference material; the implemented frontend is in `src/`.
- Scope: overview, searchable/filterable applications, three-step onboarding with an independent ID record, side-by-side identity comparison, watchlist management, officer decisions and audit history.
- **Latest user requirement:** discrepancies and watchlist risk are separate columns. Identity mismatches, missing ID records and invalid ID formats never increase watchlist risk. Unsupported ID formats are explicitly marked for manual verification.
- Watchlist risk now uses three levels: Low for no active match at 75% or higher, Medium for 75–<90%, High for ≥90%. Country is contextual evidence; it does not create a separate Critical rating. Dismissed false positives do not contribute to risk.
- Supabase remains the intended PostgreSQL host. FastAPI connects through a server-only `DATABASE_URL`; the browser has no database credentials. The backend `.env` lookup now resolves to `backend/.env` correctly.
- New frontend writes save onboarding data, screening outcomes and audit records in a transaction. Repeated screening reuses existing applicant/watchlist matches. New watchlist matches reopen reviewed applications; decisions remain in the audit history.
- Local verification uses a disposable SQLite database and synthetic data. A live Supabase connection still requires the user's project credentials. See `README.md` for setup and scope.

The older architecture and verification notes below are retained as project history; where they conflict, this section describes the current frontend workflow.

## Backend Architecture

### Decision: Use FastAPI for Backend Framework
- **Reason**: Provides native async support, automatic OpenAPI/Swagger documentation, fast execution performance, and rich Pydantic V2 integration for strict request/response data validation.
- **Alternative**: Django (too heavy/opinionated for API-first modular monolith), Flask (requires manual schemas & doc setup).
- **Trade-off**: Requires explicit structure for database transactions and repository patterns.
- **Business Impact**: Accelerates compliance API integration with Next.js frontend; ensures schema correctness.
- **Scalability Impact**: High throughput per node, stateless design makes horizontal scaling straightforward.

### Decision: Active Database Engine — PostgreSQL (`psycopg2-binary`)
- **Reason**: Enterprise standard relational database with ACID guarantees, indexed UUID lookups, robust concurrency, and production compliance readiness.
- **Configuration**: Managed via `DATABASE_URL=postgresql://user:password@host:5432/dbname` in [backend/.env](file:///d:/All_Project/Nice%20HackArena/backend/.env).
- **Alternative**: SQLite (used as fallback for isolated test environments).
- **Trade-off**: Requires running PostgreSQL server instance.
- **Business Impact**: Secure, structured, enterprise-grade storage of PII and audit logs.
- **Scalability Impact**: Full support for connection pooling (PgBouncer), read-replicas, and index optimization.

### Decision: Modular Monolith Architecture
- **Reason**: Clear layer separation (`routers` -> `services` -> `repositories` -> `database`) without microservice operational complexity during hackathon timelines.
- **Alternative**: Microservices (high overhead for deployment and inter-service communication).
- **Trade-off**: Requires discipline to maintain strict module boundaries.
- **Business Impact**: Enables fast feature delivery while preventing code spaghetti.
- **Scalability Impact**: Easy to split individual services (e.g., continuous re-screening worker) into independent microservices later if load demands.

### Decision: RapidFuzz for Deterministic Watchlist Matching (No LLM for Core Checks)
- **Reason**: High performance C++ implementation of Levenshtein and Token Sort similarity. Provides explainable numerical scores (0-100%) that compliance officers can defend to regulators.
- **Alternative**: LLM-based prompt matching (non-deterministic, slow, expensive, prone to hallucinations and non-explainable outputs).
- **Trade-off**: Requires explicit rule tuning for thresholds (e.g., 90% FUZZY_HIGH vs 75% FUZZY_MEDIUM cutoffs).
- **Business Impact**: Full regulatory compliance with auditability.
- **Scalability Impact**: Performs thousands of string comparisons per second synchronously.

### Decision: Synchronous Re-Screening with Async-Ready Service Abstraction
- **Reason**: Re-screening logic is encapsulated in `ReScreeningService`. In MVP it runs in-process or via background tasks; in production it connects to Celery/Kafka queue without changing business logic.
- **Alternative**: Full Kafka + Celery setup in MVP (unnecessary infra complexity for local demo).
- **Trade-off**: Large watchlist additions in MVP could block standard HTTP request if dataset is massive (mitigated by background task batching).
- **Business Impact**: Instant alert generation for synthetic demo datasets.
- **Scalability Impact**: Clean path to worker pool deployment.

---

## Seed Data Ingestion & Verification Record

- **Active Database Driver**: `psycopg2-binary` (PostgreSQL) installed and configured.
- **Synthetic Datasets Loaded**:
  - `applicants.csv`: 100 customer records imported
  - `id_records.csv`: 97 ID verification records imported
  - `watchlist.csv`: 30 watchlist & PEP records imported
- **Initial Automated Screening**: Screened all 100 applicants against 30 watchlist entries upon initial seed, detecting 15 potential matches requiring compliance review.
- **Test Suite Verification**: 20/20 test cases passing in `backend/tests/test_compliance_engine.py`.
