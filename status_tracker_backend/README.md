# Status Tracker Backend (Flask)

This backend provides REST APIs for:
- Authentication: signup, login, refresh, logout (integrated with Supabase Auth)
- User management: list/create (admin), get/update/delete (admin), self profile get/update
- Status CRUD: create/list/get/update/delete with ownership enforcement and admin override

Run locally:
1. Create and activate a virtualenv.
2. Install requirements: `pip install -r requirements.txt`
3. Initialize DB (SQLite by default): `FLASK_APP=run.py flask init-db`
4. Start the server: `python run.py`
5. Open API docs at `/docs`

Run tests:
- CI/non-interactive: `pytest -q`
- Locally, tests mock Supabase HTTP calls so no real Supabase project is required. Ensure at least JWT_SECRET_KEY is set or rely on tests setting it via monkeypatch.

Environment variables: see `.env.example`.

Auth via Supabase:
- Required env vars:
  - SUPABASE_URL (e.g., https://xyzcompany.supabase.co)
  - SUPABASE_KEY (recommended: service_role key, used only server-side)
  - Optional: SITE_URL (used for email confirmation redirect during signup, must be allowlisted in Supabase)
  - JWT_SECRET_KEY (for app JWTs)
  - CORS_ORIGINS (comma-separated list)
- Signup and login call Supabase REST auth endpoints. The backend issues its own JWTs for protecting internal routes.
- Local password storage/checks are disabled. Password changes must be handled through Supabase.
- Logout: provide `X-Supabase-Token` header with the user’s Supabase access token so backend can call `/auth/v1/logout`.
- Supabase Dashboard > Authentication > URL Configuration:
  - Site URL: http://localhost:3000/ (dev)
  - Additional Redirect URLs: include http://localhost:5000/** if backend sends email links

Key endpoints (prefix /api):
- POST /api/auth/signup
- POST /api/auth/login
- POST /api/auth/refresh
- POST /api/auth/logout
- GET/POST /api/users (admin)
- GET/PATCH /api/users/me
- GET/PATCH/DELETE /api/users/{id} (admin)
- GET/POST /api/statuses
- GET/PATCH/DELETE /api/statuses/{id}
