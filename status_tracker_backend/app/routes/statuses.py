from flask_smorest import Blueprint, abort
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..extensions import db
from ..models import Status
from ..schemas import StatusSchema
from ..utils import paginate_query

blp = Blueprint(
    "Statuses",
    "statuses",
    url_prefix="/api/statuses",
    description="CRUD for status items. Users can manage their own statuses; admins can manage all.",
)


def _can_access(status: Status, claims) -> bool:
    """Check if current user can access the status."""
    return status.user_id == int(claims["sub"]) or claims.get("is_admin", False)


@blp.route("")
class StatusList(MethodView):
    """List and create statuses."""

    @jwt_required()
    @blp.response(200, StatusSchema(many=True))
    @blp.doc(summary="List statuses", description="List statuses owned by the current user. Admins see all. Filter by state via ?state=open|in_progress|closed")
    def get(self):
        # PUBLIC_INTERFACE
        """List statuses with optional state filter."""
        claims = get_jwt()
        state = None
        from flask import request
        state = request.args.get("state")
        q = Status.query
        if state:
            q = q.filter(Status.state == state)
        if not claims.get("is_admin"):
            q = q.filter(Status.user_id == int(get_jwt_identity()))
        q = q.order_by(Status.created_at.desc())
        items, _ = paginate_query(q)
        return items

    @jwt_required()
    @blp.arguments(StatusSchema)
    @blp.response(201, StatusSchema)
    @blp.doc(summary="Create status", description="Create a new status owned by the current user.")
    def post(self, payload):
        # PUBLIC_INTERFACE
        """Create a status."""
        uid = int(get_jwt_identity())
        status = Status(
            title=payload["title"].strip(),
            description=payload.get("description"),
            state=payload.get("state", "open"),
            user_id=uid,
        )
        db.session.add(status)
        db.session.commit()
        return status


@blp.route("/<int:status_id>")
class StatusDetail(MethodView):
    """Retrieve, update, and delete a status."""

    @jwt_required()
    @blp.response(200, StatusSchema)
    @blp.doc(summary="Get status", description="Retrieve a status by ID, only if owned by user or admin.")
    def get(self, status_id):
        # PUBLIC_INTERFACE
        """Get a status."""
        status = Status.query.get_or_404(status_id)
        claims = get_jwt()
        if not _can_access(status, claims):
            abort(403, message="Not authorized to access this status.")
        return status

    @jwt_required()
    @blp.arguments(StatusSchema(partial=True))
    @blp.response(200, StatusSchema)
    @blp.doc(summary="Update status", description="Update fields of a status (title, description, state). Ownership or admin required.")
    def patch(self, payload, status_id):
        # PUBLIC_INTERFACE
        """Update a status."""
        status = Status.query.get_or_404(status_id)
        claims = get_jwt()
        if not _can_access(status, claims):
            abort(403, message="Not authorized to modify this status.")

        if "title" in payload:
            status.title = payload["title"].strip()
        if "description" in payload:
            status.description = payload["description"]
        if "state" in payload:
            status.state = payload["state"]
        db.session.commit()
        return status

    @jwt_required()
    @blp.response(204)
    @blp.doc(summary="Delete status", description="Delete a status by ID. Ownership or admin required.")
    def delete(self, status_id):
        # PUBLIC_INTERFACE
        """Delete a status."""
        status = Status.query.get_or_404(status_id)
        claims = get_jwt()
        if not _can_access(status, claims):
            abort(403, message="Not authorized to delete this status.")
        db.session.delete(status)
        db.session.commit()
        return ""
