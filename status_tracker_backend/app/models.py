from datetime import datetime
from werkzeug.security import generate_password_hash
from .extensions import db


class TimestampMixin:
    """Adds created_at and updated_at timestamps."""
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(db.Model, TimestampMixin):
    """User model for ownership and profile (auth handled by Supabase)."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    # Kept for backward compatibility; not used for authentication anymore
    password_hash = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    statuses = db.relationship("Status", backref="owner", lazy=True, cascade="all, delete-orphan")

    def set_password(self, raw_password: str) -> None:
        """Deprecated: Passwords are managed by Supabase. Retained for compatibility with existing DB."""
        if raw_password:
            self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Deprecated: Always returns False because Supabase is the source of truth."""
        return False


class Status(db.Model, TimestampMixin):
    """Status entity representing a trackable item."""
    __tablename__ = "statuses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    state = db.Column(db.String(50), nullable=False, default="open")  # e.g., open, in_progress, closed
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
