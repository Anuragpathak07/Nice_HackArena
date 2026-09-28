-- Run after FastAPI/seed_data creates the tables in your Supabase project.
-- This app uses a server-side PostgreSQL connection, not public browser Data API access.
begin;
alter table public.applicants enable row level security;
alter table public.id_records enable row level security;
alter table public.watchlist enable row level security;
alter table public.screening_results enable row level security;
alter table public.alerts enable row level security;
alter table public.audit_logs enable row level security;
revoke all on public.applicants, public.id_records, public.watchlist,
  public.screening_results, public.alerts, public.audit_logs from anon, authenticated;
commit;
