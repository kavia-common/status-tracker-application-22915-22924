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
    id = fields.Int(dump_only=True, description="Unique identifier of the user")
    email = fields.Email(required=True, description="User email (unique)")
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120), description="Full name")
    is_active = fields.Bool(dump_only=True, description="Is the user active")
    is_admin = fields.Bool(dump_only=True, description="Is the user an admin")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class UserCreateSchema(ma.Schema):
    email = fields.Email(required=True, description="User email (unique)")
    name = fields.Str(required=True, validate=validate.Length(min=1, max=120), description="Full name")
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=6), description="Password")


class UserUpdateSchema(ma.Schema):
    name = fields.Str(required=False, validate=validate.Length(min=1, max=120), description="Full name")
    password = fields.Str(required=False, load_only=True, validate=validate.Length(min=6), description="New password")
    is_active = fields.Bool(required=False, description="Activate/Deactivate user")
    is_admin = fields.Bool(required=False, description="Promote/Demote admin (admin only)")


class AuthLoginSchema(ma.Schema):
    email = fields.Email(required=True, description="Email for login")
    password = fields.Str(required=True, load_only=True, description="Password")


class AuthTokensSchema(ma.Schema):
    access_token = fields.Str(description="JWT access token")
    refresh_token = fields.Str(description="JWT refresh token")


class StatusSchema(ma.Schema):
    id = fields.Int(dump_only=True, description="Status ID")
    title = fields.Str(required=True, validate=validate.Length(min=1, max=200), description="Title")
    description = fields.Str(allow_none=True, description="Detailed description")
    state = fields.Str(required=True, validate=validate.OneOf(["open", "in_progress", "closed"]), description="State")
    user_id = fields.Int(dump_only=True, description="Owner ID")
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
