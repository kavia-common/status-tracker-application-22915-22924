from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..extensions import db
from ..models import User
from ..schemas import UserBaseSchema, UserCreateSchema, UserUpdateSchema, PaginationMetadataSchema
from ..utils import paginate_query, require_admin

blp = Blueprint(
    "Users",
    "users",
    url_prefix="/api/users",
    description="User management endpoints. Admin can manage users; users can manage own profile.",
)


@blp.route("")
class UsersList(MethodView):
    """List and create users (admin)."""

    @jwt_required()
    @blp.response(200, UserBaseSchema(many=True))
    @blp.alt_response(200, schema=PaginationMetadataSchema, description="Returns users with pagination metadata in X-Pagination header")
    @blp.doc(summary="List users", description="Admin-only list of users with pagination.")
    def get(self):
        # PUBLIC_INTERFACE
        """List users (admin only)."""
        require_admin()
        items, meta = paginate_query(User.query.order_by(User.created_at.desc()))
        # Include pagination metadata via header-like structure: flask-smorest does not manage headers easily
        # Clients can compute pagination based on response length and optional meta endpoint; for simplicity, return as object
        return items  # In real app, consider wrapping with {"items": items, "meta": meta}

    @jwt_required()
    @blp.arguments(UserCreateSchema)
    @blp.response(201, UserBaseSchema)
    @blp.doc(summary="Create user", description="Admin-only create a new user.")
    def post(self, payload):
        # PUBLIC_INTERFACE
        """Create user (admin only)."""
        require_admin()
        email = payload["email"].lower().strip()
        name = payload["name"].strip()
        password = payload["password"]

        if User.query.filter_by(email=email).first():
            abort(409, message="Email already registered.")

        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user


@blp.route("/me")
class Me(MethodView):
    """Get or update current user profile."""

    @jwt_required()
    @blp.response(200, UserBaseSchema)
    @blp.doc(summary="Get current user", description="Fetch the profile of the authenticated user.")
    def get(self):
        # PUBLIC_INTERFACE
        """Get self profile."""
        uid = int(get_jwt_identity())
        user = User.query.get_or_404(uid)
        return user

    @jwt_required()
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserBaseSchema)
    @blp.doc(summary="Update current user", description="Update name or password for the authenticated user.")
    def patch(self, payload):
        # PUBLIC_INTERFACE
        """Update self profile."""
        uid = int(get_jwt_identity())
        user = User.query.get_or_404(uid)
        if "name" in payload:
            user.name = payload["name"].strip()
        if "password" in payload and payload["password"]:
            user.set_password(payload["password"])
        db.session.commit()
        return user


@blp.route("/<int:user_id>")
class UserDetail(MethodView):
    """Retrieve, update, or delete a specific user (admin)."""

    @jwt_required()
    @blp.response(200, UserBaseSchema)
    @blp.doc(summary="Get user", description="Admin-only fetch by user ID.")
    def get(self, user_id):
        # PUBLIC_INTERFACE
        """Get user by id (admin)."""
        require_admin()
        user = User.query.get_or_404(user_id)
        return user

    @jwt_required()
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserBaseSchema)
    @blp.doc(summary="Update user", description="Admin-only update fields including is_active and is_admin.")
    def patch(self, payload, user_id):
        # PUBLIC_INTERFACE
        """Update user (admin)."""
        require_admin()
        user = User.query.get_or_404(user_id)
        if "name" in payload:
            user.name = payload["name"].strip()
        if "password" in payload and payload["password"]:
            user.set_password(payload["password"])
        if "is_active" in payload:
            user.is_active = bool(payload["is_active"])
        if "is_admin" in payload:
            user.is_admin = bool(payload["is_admin"])
        db.session.commit()
        return user

    @jwt_required()
    @blp.response(204)
    @blp.doc(summary="Delete user", description="Admin-only delete user by ID.")
    def delete(self, user_id):
        # PUBLIC_INTERFACE
        """Delete user (admin)."""
        require_admin()
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return ""
