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

Environment variables: see `.env.example`.

Auth via Supabase:
- Required env vars:
  - SUPABASE_URL
  - SUPABASE_KEY
  - Optional: SITE_URL (used for email confirmation redirect during signup)
- Signup and login call Supabase REST auth endpoints. The backend issues its own JWTs for protecting internal routes.
- Local password storage/checks are disabled. Password changes must be handled through Supabase.
- To sign out, the backend can revoke Supabase session if the client provides `X-Supabase-Token` header with the current Supabase access token.

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
