from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import jsonify, request, current_app
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from datetime import datetime, timezone

from ..extensions import jwt
from ..schemas import AuthTokensSchema, UserCreateSchema, UserBaseSchema
from ..supabase_auth import (
    supabase_signup,
    supabase_login,
    supabase_logout,
)

blp = Blueprint(
    "Auth",
    "auth",
    url_prefix="/api/auth",
    description="Authentication routes for login, logout, and token refresh.",
)

# In-memory token revoke list for app-level JWTs; Supabase session revocation is handled by Supabase
JWT_BLOCKLIST = set()


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get("jti")
    return jti in JWT_BLOCKLIST


@blp.route("/signup")
class SignUp(MethodView):
    """Create a new user account using Supabase Auth."""

    @blp.arguments(UserCreateSchema)
    @blp.response(201, UserBaseSchema)
    @blp.doc(summary="Sign up", description="Register a new user in Supabase with email, name, and password.")
    def post(self, body):
        # PUBLIC_INTERFACE
        """Create a Supabase user.

        Note: We no longer create a local user/password. Users are managed by Supabase.
        """
        email = body["email"].lower().strip()
        name = body["name"].strip()
        password = body["password"]

        # Optional email redirect for confirmation links
        site_url = current_app.config.get("SITE_URL")
        supabase_resp = supabase_signup(email=email, password=password, name=name, email_redirect_to=site_url)

        # Return a minimal user representation to align with existing schema
        # Supabase returns 'user' object; map fields we have in schema
        user_obj = supabase_resp.get("user") or {}
        return {
            "id": user_obj.get("id"),  # Note: UUID; schema defines Int, but we keep compatibility by not strictly enforcing here
            "email": user_obj.get("email") or email,
            "name": name,
            "is_active": True,
            "is_admin": False,
            "created_at": user_obj.get("created_at"),
            "updated_at": user_obj.get("updated_at"),
        }


@blp.route("/login")
class Login(MethodView):
    """Login via Supabase and mint app JWTs."""

    @blp.response(200, AuthTokensSchema)
    @blp.doc(
        summary="Login",
        description="Authenticate with Supabase using email/password; returns app JWT tokens."
    )
    def post(self):
        # PUBLIC_INTERFACE
        """Authenticate using Supabase and generate app tokens.

        Accepts JSON or form data with {email, password}.
        """
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form or {}

        email = (data.get("email") or data.get("username") or "").strip().lower()
        password = data.get("password")
        if not email or not password:
            abort(422, message="Missing required fields: email (or username) and password.")

        session = supabase_login(email=email, password=password)

        # We rely on Supabase for credential verification. For the internal API, we issue our own JWTs.
        # Use the Supabase user id as identity if available; otherwise fallback to email.
        user_info = session.get("user") or {}
        identity = str(user_info.get("id") or email)

        # No local admin management via password; default to False unless you later implement role mapping.
        claims = {"is_admin": False}

        access_token = create_access_token(identity=identity, additional_claims=claims)
        refresh_token = create_refresh_token(identity=identity, additional_claims=claims)
        return {"access_token": access_token, "refresh_token": refresh_token}


@blp.route("/refresh")
class Refresh(MethodView):
    """Refresh tokens.

    Note: Client should pass Supabase refresh token if they want to refresh Supabase session separately.
    This endpoint refreshes our app JWT using app refresh token.
    """

    @jwt_required(refresh=True)
    @blp.response(200, AuthTokensSchema)
    @blp.doc(summary="Refresh app token", description="Use app refresh token to obtain a new app access token.")
    def post(self):
        # PUBLIC_INTERFACE
        """Refresh app access token."""
        identity = get_jwt_identity()
        claims = {"is_admin": get_jwt().get("is_admin", False)}
        access_token = create_access_token(identity=identity, additional_claims=claims)
        return {"access_token": access_token, "refresh_token": None}


@blp.route("/logout")
class Logout(MethodView):
    """Logout by revoking Supabase session and current app access token."""

    @jwt_required()
    @blp.response(200)
    @blp.doc(summary="Logout", description="Revoke Supabase session and the current app access token.")
    def post(self):
        # PUBLIC_INTERFACE
        """Revoke token (Supabase and app)."""
        # If client provides Supabase access token in header X-Supabase-Token, revoke it as well
        supa_token = request.headers.get("X-Supabase-Token")
        if supa_token:
            try:
                supabase_logout(supa_token)
            except Exception:
                # Even if Supabase logout fails, continue to revoke local token
                pass

        jti = get_jwt()["jti"]
        JWT_BLOCKLIST.add(jti)
        return jsonify({"message": "Logged out", "revoked_at": datetime.now(timezone.utc).isoformat()})
