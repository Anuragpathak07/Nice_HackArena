# Clear · KYC & AML workspace

A minimal white compliance frontend with applicant onboarding, identity comparisons, watchlist screening, officer decisions and an audit trail. React + TypeScript + Vite serves the interface; the existing FastAPI + SQLAlchemy backend connects to **Supabase PostgreSQL**.

## Run locally

Requires Node 22.12+ and Python 3.10+. From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
npm install
Copy-Item backend/.env.example backend/.env
```

Set `DATABASE_URL` in `backend/.env` to the **Session pooler** PostgreSQL connection string from your Supabase project's **Connect** panel, with your database password URL-encoded and `?sslmode=require`. This is a database connection string, not a Supabase API URL or publishable key. The backend loads this file regardless of the working directory.

```powershell
npm run seed
npm run dev
```

Open **http://127.0.0.1:5173**. API documentation: http://127.0.0.1:8000/docs. `npm run dev` starts both processes; keep the virtual environment activated. The seed command creates the six tables and imports the supplied synthetic records. Re-running screening reuses existing match records rather than duplicating alerts.

Without a `DATABASE_URL`, the inherited SQLite fallback is available for a local synthetic-data demo. For an explicit disposable demo, set `$env:DATABASE_URL='sqlite:///./demo.db'` before seeding and starting. This is not a Supabase connection. No hosted project or credentials are bundled.

## Supabase data access

The browser calls FastAPI; only the backend connects to Supabase. No database password or service-role key is sent to the client. After initial table creation, run `supabase/restrict_browser_access.sql` in the Supabase SQL editor to keep these tables inaccessible through the public Data API. The backend's PostgreSQL connection continues to work.

Connection guidance: [Supabase PostgreSQL connections](https://supabase.com/docs/guides/database/connecting-to-postgres) and [SQLAlchemy with Supabase](https://supabase.com/docs/guides/troubleshooting/using-sqlalchemy-with-supabase-FUqebT).

## Two independent signals

**Discrepancies** compare the full name, date of birth and complete address with an independently entered ID record. Missing records, partial names, different values and invalid supported ID formats are findings. Names allow title removal and reordered words; addresses normalize punctuation and spacing but cannot pass just because one street word overlaps. Format rules exist for India, the US and the UAE; other countries explicitly require manual verification. A format check does not authenticate an ID.

**Watchlist risk** uses the strongest non-dismissed name match: Low below 75%, Medium from 75% to below 90%, High from 90%. Exact and normalized matches score 100%. Identity discrepancies, occupation and income do not change this rating. Similarity is a review signal, not confirmation that two people are the same. These are demo rules, not a certified compliance model.

New applications save the applicant and ID together, compare identity data and run watchlist screening. All applications require a human decision. Officers can approve or reject with their name and explanation, or dismiss a watchlist false positive. New watchlist entries re-screen existing applicants and reopen applications with new matches. Historical decisions remain in the audit log. Re-screening currently runs synchronously for this small dataset.

## Verification

```powershell
npm run build
npm run test:api
npx playwright install chromium
npx playwright test
```

Browser tests expect the app already running on port 5173 against an isolated local synthetic-data database. They create test applications, decisions and a watchlist entry. Never run them against a shared or production database. Python tests force isolated SQLite databases before importing the application.

## Scope

This is a local hackathon review workspace. Reviewer names are entered manually; authentication and role enforcement are not implemented. Do not expose the API publicly with real customer data until authenticated officer access is added. Supabase hosting is supported by configuration but must be verified with your actual project. Frontend files live in `src/`; frontend workflow endpoints in `backend/app/api/v1/workspace.py`.
