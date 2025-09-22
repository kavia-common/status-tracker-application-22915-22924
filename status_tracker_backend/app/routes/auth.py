from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from datetime import datetime, timezone

from ..extensions import db, jwt
from ..models import User
from ..schemas import AuthTokensSchema, UserCreateSchema, UserBaseSchema

blp = Blueprint(
    "Auth",
    "auth",
    url_prefix="/api/auth",
    description="Authentication routes for login, logout, and token refresh.",
)

# In-memory token revoke list for demo; replace with persistent store in production
JWT_BLOCKLIST = set()


@jwt.token_in_blocklist_loader
def check_if_token_revoked(jwt_header, jwt_payload):
    jti = jwt_payload.get("jti")
    return jti in JWT_BLOCKLIST


@blp.route("/signup")
class SignUp(MethodView):
    """Create a new user account. Intended for initial setup or admin-driven creation."""

    @blp.arguments(UserCreateSchema)
    @blp.response(201, UserBaseSchema)
    @blp.doc(summary="Sign up", description="Create a new user with email, name, and password.")
    def post(self, body):
        # PUBLIC_INTERFACE
        """Create a user."""
        email = body["email"].lower().strip()
        name = body["name"].strip()
        password = body["password"]

        if User.query.filter_by(email=email).first():
            abort(409, message="Email already registered.")

        user = User(email=email, name=name)
        user.set_password(password)
        # First user becomes admin to bootstrap system
        if User.query.count() == 0:
            user.is_admin = True

        db.session.add(user)
        db.session.commit()
        return user


@blp.route("/login")
class Login(MethodView):
    """Login to obtain access and refresh tokens."""

    # Keep response schema for success. We will manually parse payload to be flexible with frontend variations.
    @blp.response(200, AuthTokensSchema)
    @blp.doc(
        summary="Login",
        description="Authenticate with email/username and password; accepts JSON or form-encoded bodies. Returns JWT tokens."
    )
    def post(self):
        # PUBLIC_INTERFACE
        """Authenticate and generate tokens.

        Accepts:
        - application/json: {email, password} or {username, password}
        - application/x-www-form-urlencoded or multipart/form-data: email/password or username/password
        """
        # Try JSON first
        email = None
        password = None

        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            # Support form submissions
            data = request.form or {}

        # Map common aliases
        email = (data.get("email") or data.get("username") or "").strip().lower()
        password = data.get("password")

        # Validate presence
        if not email or not password:
            abort(422, message="Missing required fields: email (or username) and password.")

        user = User.query.filter_by(email=email, is_active=True).first()
        if not user or not user.check_password(password):
            abort(401, message="Invalid email or password.")

        claims = {"is_admin": user.is_admin}
        access_token = create_access_token(identity=str(user.id), additional_claims=claims)
        refresh_token = create_refresh_token(identity=str(user.id), additional_claims=claims)
        return {"access_token": access_token, "refresh_token": refresh_token}


@blp.route("/refresh")
class Refresh(MethodView):
    """Refresh access token using a valid refresh token."""

    @jwt_required(refresh=True)
    @blp.response(200, AuthTokensSchema)
    @blp.doc(summary="Refresh token", description="Use refresh token to obtain a new access token.")
    def post(self):
        # PUBLIC_INTERFACE
        """Refresh access token."""
        identity = get_jwt_identity()
        claims = {"is_admin": get_jwt().get("is_admin", False)}
        access_token = create_access_token(identity=identity, additional_claims=claims)
        return {"access_token": access_token, "refresh_token": None}


@blp.route("/logout")
class Logout(MethodView):
    """Logout by revoking the current access token."""

    @jwt_required()
    @blp.response(200)
    @blp.doc(summary="Logout", description="Revoke the current access token.")
    def post(self):
        # PUBLIC_INTERFACE
        """Revoke token."""
        jti = get_jwt()["jti"]
        JWT_BLOCKLIST.add(jti)
        return jsonify({"message": "Logged out", "revoked_at": datetime.now(timezone.utc).isoformat()})
