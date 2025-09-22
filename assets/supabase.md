# Supabase Integration Guide

This backend uses Supabase Auth for signup, login, session revoke, and user retrieval. The backend mints its own JWTs to protect internal APIs.

Environment variables (set these in your backend .env):
- SUPABASE_URL: Your Supabase project URL (e.g., https://xyzcompany.supabase.co)
- SUPABASE_KEY: Use the service_role key in server-side flows that call Admin Auth endpoints (recommended). Using an anon key may fail for certain admin endpoints like signup.
- SITE_URL: Used to set email redirect URL for signup confirmations (e.g., http://localhost:5000/ during local dev)
- JWT_SECRET_KEY: Secret for app-level JWT tokens
- CORS_ORIGINS: Comma-separated list of allowed origins for the backend

Auth behavior:
- POST /api/auth/signup
  - Calls Supabase POST /auth/v1/signup with email, password, and metadata {name}. If SITE_URL is set, it is sent as email_redirect_to for confirmation links.
- POST /api/auth/login
  - Calls Supabase POST /auth/v1/token?grant_type=password with {email, password}. On success, the backend issues app-level access/refresh tokens.
- POST /api/auth/refresh
  - Refreshes the app-level JWT using the refresh token. Supabase session refresh is not proxied here.
- POST /api/auth/logout
  - If X-Supabase-Token header is provided with the Supabase access_token, the backend calls POST /auth/v1/logout to revoke the Supabase session; the app token is also revoked.

Important headers:
- For Admin calls (signup/password grant), backend uses:
  - headers: { "apikey": SUPABASE_KEY, "Authorization": "Bearer " + SUPABASE_KEY }
- For user-context calls (logout, user info), backend uses:
  - headers: { "apikey": SUPABASE_KEY, "Authorization": "Bearer " + <user access_token> }

Allowed Redirects in Supabase Dashboard:
1) Go to Authentication > URL Configuration
2) Site URL:
   - Development: http://localhost:3000/ (frontend)
   - Backend callbacks may use SITE_URL if you send links from the backend: http://localhost:5000/
3) Additional Redirect URLs:
   - http://localhost:3000/**
   - http(s)://your-prod-frontend-domain/**
   - http(s)://your-prod-backend-domain/**
4) If you use email confirmations, ensure the SITE_URL value is included in the redirect allowlist.

Database schema (public):
- users
  - id uuid primary key default gen_random_uuid()
  - email text not null unique
  - name text not null
  - is_active boolean not null default true
  - is_admin boolean not null default false
  - created_at timestamptz not null default now()
  - updated_at timestamptz not null default now()
- statuses
  - id bigserial primary key
  - title text not null
  - description text null
  - state text not null default 'open'
  - user_id uuid not null references public.users(id) on delete cascade
  - created_at timestamptz not null default now()
  - updated_at timestamptz not null default now()

Recommended triggers:
```sql
create or replace function public.set_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

drop trigger if exists set_users_updated_at on public.users;
create trigger set_users_updated_at before update on public.users
for each row execute function public.set_updated_at();

drop trigger if exists set_statuses_updated_at on public.statuses;
create trigger set_statuses_updated_at before update on public.statuses
for each row execute function public.set_updated_at();
```

Row Level Security (RLS):
```sql
alter table public.users enable row level security;
alter table public.statuses enable row level security;

-- users: only the authenticated user can view/update their profile row
create policy if not exists users_select_own on public.users for select using (id = auth.uid());
create policy if not exists users_update_own on public.users for update using (id = auth.uid());

-- statuses: owner can CRUD
create policy if not exists statuses_select_own on public.statuses for select using (user_id = auth.uid());
create policy if not exists statuses_insert_own on public.statuses for insert with check (user_id = auth.uid());
create policy if not exists statuses_update_own on public.statuses for update using (user_id = auth.uid());
create policy if not exists statuses_delete_own on public.statuses for delete using (user_id = auth.uid());
```

Security notes:
- Prefer using SUPABASE_KEY = service_role in the backend to call Admin Auth endpoints securely.
- Never expose service_role key to clients or frontend code.
- Ensure all redirect URLs used by the backend are allowlisted in Supabase Dashboard.

Local development setup:
1. Create backend .env with:
   - SUPABASE_URL=...
   - SUPABASE_KEY=...
   - SITE_URL=http://localhost:5000/
   - JWT_SECRET_KEY=...
   - CORS_ORIGINS=http://localhost:3000
2. In Supabase Dashboard, add http://localhost:3000/** and http://localhost:5000/** to Redirect URLs.
3. Apply the SQL above in the Supabase SQL editor if not already applied.
4. Run backend: `python run.py`
5. The backend endpoints are documented in status_tracker_backend/README.md.
