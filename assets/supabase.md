# Supabase Integration Guide

This project uses Supabase Auth for user signup, login, token refresh, and logout.

Environment variables (set these in your .env):
- SUPABASE_URL: Your Supabase project URL (e.g., https://xyzcompany.supabase.co)
- SUPABASE_KEY: A key with permissions to call the auth endpoints (service role or anon key depending on your security model)
- SITE_URL (optional): Used to set email redirect URL for signup confirmation emails

Behavior:
- POST /api/auth/signup: Calls Supabase /auth/v1/signup with email, password, and name (as user metadata). Optionally uses SITE_URL for email redirect.
- POST /api/auth/login: Calls Supabase /auth/v1/token?grant_type=password to verify credentials. The backend then issues app-level JWTs to protect internal endpoints.
- POST /api/auth/refresh: Refreshes the app-level JWT (not Supabase token). To refresh Supabase session, call Supabase directly or extend this backend to passthrough.
- POST /api/auth/logout: If the request includes X-Supabase-Token header with the Supabase access token, the backend calls Supabase /auth/v1/logout to revoke it, and also revokes the app-level token.

Notes:
- The local database keeps a lightweight User profile for app features like status ownership. Passwords are no longer stored nor used for authentication.
- When identity is a Supabase UUID, mapping to local user IDs may be required for creating statuses. Currently, creating statuses requires a numeric local user_id. Ensure a local user record exists for your Supabase account and align identities as needed.
