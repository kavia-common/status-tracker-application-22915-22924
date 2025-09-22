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
        return items

    @jwt_required()
    @blp.arguments(UserCreateSchema)
    @blp.response(201, UserBaseSchema)
    @blp.doc(summary="Create user", description="Admin-only create a new user (local record only; auth handled by Supabase).")
    def post(self, payload):
        # PUBLIC_INTERFACE
        """Create user (admin only). Local record only.

        Note: Authentication and password storage are handled by Supabase now.
        """
        require_admin()
        email = payload["email"].lower().strip()
        name = payload["name"].strip()

        if User.query.filter_by(email=email).first():
            abort(409, message="Email already registered.")

        user = User(email=email, name=name)
        # Do not set or store local passwords anymore
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
        uid = get_jwt_identity()
        # local table may not have UUIDs; try to fallback with email if needed
        user = None
        try:
            # if identity was numeric, try integer lookup
            user = User.query.get(int(uid))
        except Exception:
            # Otherwise fall back to email
            user = User.query.filter_by(email=str(uid)).first()
        if not user:
            abort(404, message="User profile not found in local store.")
        return user

    @jwt_required()
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserBaseSchema)
    @blp.doc(summary="Update current user", description="Update name for the authenticated user. Password changes must be done via Supabase.")
    def patch(self, payload):
        # PUBLIC_INTERFACE
        """Update self profile (name only)."""
        uid = get_jwt_identity()
        user = None
        try:
            user = User.query.get(int(uid))
        except Exception:
            user = User.query.filter_by(email=str(uid)).first()
        if not user:
            abort(404, message="User profile not found in local store.")
        if "name" in payload:
            user.name = payload["name"].strip()
        # Ignore password updates here; handled by Supabase outside this API
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
    @blp.doc(summary="Update user", description="Admin-only update fields including is_active and is_admin. Password not managed locally.")
    def patch(self, payload, user_id):
        # PUBLIC_INTERFACE
        """Update user (admin)."""
        require_admin()
        user = User.query.get_or_404(user_id)
        if "name" in payload:
            user.name = payload["name"].strip()
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
