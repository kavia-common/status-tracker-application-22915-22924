import os
import json
from typing import Optional, Tuple, Dict, Any
import requests
from werkzeug.exceptions import Unauthorized, BadRequest, InternalServerError


def _get_supabase_env() -> Tuple[str, str]:
    """Fetch Supabase URL and service key from environment, raising if missing."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise InternalServerError("Supabase configuration missing. Set SUPABASE_URL and SUPABASE_KEY in environment.")
    return url.rstrip("/"), key


def _default_headers(api_key: str) -> Dict[str, str]:
    """Common headers for Supabase auth API calls."""
    return {
        "apikey": api_key,
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


# PUBLIC_INTERFACE
def supabase_signup(email: str, password: str, name: Optional[str] = None, email_redirect_to: Optional[str] = None) -> Dict[str, Any]:
    """Register a user in Supabase Auth.

    Returns a dict with user/session per Supabase admin API behavior.
    """
    base_url, api_key = _get_supabase_env()
    payload: Dict[str, Any] = {"email": email, "password": password}
    if name:
        payload["data"] = {"name": name}
    if email_redirect_to:
        payload["email_redirect_to"] = email_redirect_to

    resp = requests.post(
        f"{base_url}/auth/v1/signup",
        headers=_default_headers(api_key),
        data=json.dumps(payload),
        timeout=15,
    )
    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}
        raise BadRequest(data.get("msg") or data.get("error_description") or data.get("error") or "Signup failed")
    return resp.json()


# PUBLIC_INTERFACE
def supabase_login(email: str, password: str) -> Dict[str, Any]:
    """Login the user using Supabase Auth to obtain a session.

    Returns dict including 'access_token', 'refresh_token', and 'user' if successful.
    """
    base_url, api_key = _get_supabase_env()
    payload = {"email": email, "password": password}
    resp = requests.post(
        f"{base_url}/auth/v1/token?grant_type=password",
        headers=_default_headers(api_key),
        data=json.dumps(payload),
        timeout=15,
    )
    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}
        raise Unauthorized(data.get("error_description") or data.get("msg") or data.get("error") or "Invalid credentials")
    return resp.json()


# PUBLIC_INTERFACE
def supabase_refresh(refresh_token: str) -> Dict[str, Any]:
    """Refresh the Supabase session using a refresh_token."""
    base_url, api_key = _get_supabase_env()
    payload = {"refresh_token": refresh_token}
    resp = requests.post(
        f"{base_url}/auth/v1/token?grant_type=refresh_token",
        headers=_default_headers(api_key),
        data=json.dumps(payload),
        timeout=15,
    )
    if resp.status_code >= 400:
        try:
            data = resp.json()
        except Exception:
            data = {"error": resp.text}
        raise Unauthorized(data.get("error_description") or data.get("msg") or data.get("error") or "Refresh failed")
    return resp.json()


# PUBLIC_INTERFACE
def supabase_logout(access_token: str) -> None:
    """Logout (revoke) the current access token in Supabase."""
    base_url, api_key = _get_supabase_env()
    # For signout, the Authorization header should be the user's access_token
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {access_token}",
    }
    resp = requests.post(f"{base_url}/auth/v1/logout", headers=headers, timeout=15)
    # Supabase returns 204 No Content for success; treat 401/400 as errors
    if resp.status_code not in (200, 204):
        raise Unauthorized("Logout failed")


# PUBLIC_INTERFACE
def supabase_get_user(access_token: str) -> Dict[str, Any]:
    """Retrieve current user using Supabase access token. Raises if invalid."""
    base_url, api_key = _get_supabase_env()
    headers = {
        "apikey": api_key,
        "Authorization": f"Bearer {access_token}",
    }
    resp = requests.get(f"{base_url}/auth/v1/user", headers=headers, timeout=15)
    if resp.status_code >= 400:
        raise Unauthorized("Invalid or expired token")
    return resp.json()
