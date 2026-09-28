# HACKARENA DECISION LOG

## Backend Architecture

### Decision: Use FastAPI for Backend Framework
- **Reason**: Native async support, automatic OpenAPI/Swagger documentation, high execution performance, and rich Pydantic V2 integration for strict request/response data validation.
- **Alternative**: Django (too heavy/opinionated for API-first modular monolith), Flask (requires manual schemas & doc setup).
- **Trade-off**: Requires explicit structure for database transactions and repository patterns.
- **Business Impact**: Accelerates compliance API integration with Next.js frontend; ensures schema correctness.
- **Scalability Impact**: High throughput per node, stateless design makes horizontal scaling straightforward.

### Decision: Active Database Engine — Supabase PostgreSQL (`psycopg2-binary`)
- **Reason**: Enterprise standard relational database with ACID guarantees, indexed UUID lookups, robust concurrency, and production compliance readiness.
- **Configuration**: Managed via `DATABASE_URL=postgresql://...` in [backend/.env](file:///d:/All_Project/Nice%20HackArena/backend/.env).
- **Alternative**: SQLite (used as fallback for isolated test environments).
- **Trade-off**: Requires running PostgreSQL server instance.
- **Business Impact**: Secure, structured, enterprise-grade storage of PII and audit logs.
- **Scalability Impact**: Full support for connection pooling (PgBouncer), read-replicas, and index optimization.

### Decision: Enhanced 10-Table Relational Schema
- **Reason**: Fully supports Feature 5 (KYC Impact Radar), before/after state diff preservation, structured evidence matrix collection, and compliance case workflows without opaque JSON blobs.
- **Entities**: `applicants`, `id_records`, `watchlist`, `screening_results`, `screening_evidence`, `impact_analyses`, `impact_results`, `compliance_alerts`, `compliance_cases`, `audit_logs`.
- **Alternative**: 5-table flat model (lacked before/after state diffs and evidence signal tracking).
- **Trade-off**: Slightly higher schema complexity.
- **Business Impact**: Complete explainability and auditability for regulators.
- **Scalability Impact**: Indexes added on `status`, `risk_level`, `normalized_name`, `application_id`, `analysis_id`.

### Decision: RapidFuzz + Structured Evidence Matrix for Deterministic Screening
- **Reason**: High performance C++ implementation of Levenshtein and Token Sort similarity. Stores explicit evidence tuples (`NAME_SIMILARITY`, `DOB_MATCH`, `COUNTRY_MATCH`, `ADDRESS_SIMILARITY`) for 100% explainability.
- **Alternative**: Black-box LLM matching (non-deterministic, slow, expensive, prone to hallucinations and non-explainable outputs).
- **Trade-off**: Requires rule tuning for thresholds (e.g., 90% FUZZY_HIGH vs 75% FUZZY_MEDIUM cutoffs).
- **Business Impact**: Full regulatory compliance with evidence signal transparency.
- **Scalability Impact**: Performs thousands of string comparisons per second synchronously.

### Decision: Groq (`llama-3.3-70b-versatile`) for Isolated AI Case Summarization
- **Reason**: Extremely fast inference speed via Groq's LPU infrastructure. Used strictly for post-screening narrative generation and synthesizing compliance findings for compliance officers.
- **Alternative**: OpenAI / Gemini (slower response time for dashboard API endpoints).
- **Trade-off**: Isolated behind service interface with deterministic fallback so core compliance workflows do not depend on external AI availability.
- **Business Impact**: Saves compliance officers time by turning raw data into executive risk reports.
- **Scalability Impact**: Asynchronous or non-blocking call via API endpoint `POST /api/applicants/{id}/explain`.

### Decision: KYC Impact Radar Pipeline (Feature 5 Core)
- **Reason**: When a watchlist entry changes, executes a 9-stage data transformation pipeline (Analysis Trigger -> Candidate Pre-filtering -> Deterministic Matching -> Evidence -> Risk Recalculation -> Before/After Diff -> Recommended Action Engine -> Alert/Case Generation -> Immutable Audit Log).
- **Alternative**: Simple re-screening loop (lacks state diffs, impact metrics, and recommendation engine).
- **Trade-off**: Requires tracking `before` state vs `after` state in `impact_results` table.
- **Business Impact**: Answers the 3 vital compliance questions: WHAT changed? WHO is affected? WHAT should I do?
- **Scalability Impact**: Idempotent execution design allows moving to Celery/Kafka queue workers in production seamlessly.

---

## Seed Data Ingestion & Verification Record

- **Active Database Driver**: `psycopg2-binary` (Supabase PostgreSQL Cloud).
- **AI Integration**: `groq` python SDK integrated with `llama-3.3-70b-versatile` model in [backend/app/services/llm_service.py](file:///d:/All_Project/Nice%20HackArena/backend/app/services/llm_service.py).
- **Synthetic Datasets Loaded**:
  - `applicants.csv`: 100 customer records imported
  - `id_records.csv`: 97 ID verification records imported
  - `watchlist.csv`: 30 watchlist & PEP records imported
- **KYC Impact Radar Execution**: Successfully created 30 impact analyses, evaluated all 100 applicants against 30 watchlist entries, preserved before/after state diffs, generated evidence signals, and recorded audit logs in Supabase PostgreSQL.
- **Test Suite Verification**: 20/20 test cases passing in `backend/tests/test_compliance_engine.py`.
