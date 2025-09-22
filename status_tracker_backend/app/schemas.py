from marshmallow import fields, validate
from .extensions import ma


class PaginationMetadataSchema(ma.Schema):
    total = fields.Int()
    total_pages = fields.Int()
    first_page = fields.Int()
    last_page = fields.Int()
    page = fields.Int()
    previous_page = fields.Int(allow_none=True)
    next_page = fields.Int(allow_none=True)


class UserBaseSchema(ma.Schema):
    id = fields.Int(dump_only=True, description="Unique identifier of the user (local DB integer). Note: Supabase uses UUIDs.")
    email = fields.Email(required=True, description="User email (unique)")
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120), description="Full name")
    is_active = fields.Bool(dump_only=True, description="Is the user active")
    is_admin = fields.Bool(dump_only=True, description="Is the user an admin")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserCreateSchema(ma.Schema):
    email = fields.Email(required=True, description="User email (unique)")
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120), description="Full name")
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6), description="Password (stored in Supabase, not locally)")


class UserUpdateSchema(ma.Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=120), description="Full name")
    password = fields.Str(required=False, load_only=True, validate=validate.Length(min=6), description="New password (managed via Supabase)")
    is_active = fields.Bool(required=False, description="Activate/Deactivate user")
    is_admin = fields.Bool(required=False, description="Promote/Demote admin (admin only)")


class AuthLoginSchema(ma.Schema):
    email = fields.Email(required=True, description="Email for login")
    password = fields.Str(required=True, load_only=True, description="Password (verified by Supabase)")


class AuthTokensSchema(ma.Schema):
    access_token = fields.Str(description="App JWT access token")
    refresh_token = fields.Str(description="App JWT refresh token")


class StatusSchema(ma.Schema):
    id = fields.Int(dump_only=True, description="Status ID")
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200), description="Title")
    description = fields.Str(allow_none=True, description="Detailed description")
    state = fields.Str(required=True, validate=validate.OneOf(["open", "in_progress", "closed"]), description="State")
    user_id = fields.Int(dump_only=True, description="Owner ID (local DB)")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
