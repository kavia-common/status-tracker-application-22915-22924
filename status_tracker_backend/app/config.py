import os
from datetime import timedelta


class Config:
    """Base Flask configuration using environment variables. Avoids hardcoding secrets."""
    # Database URL, e.g., sqlite:///app.db or postgresql+psycopg2://user:pass@host:port/dbname
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT settings
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-secret")  # MUST be overridden in production via .env
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "60")))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "7")))

    # API documentation
    API_TITLE = "Status Tracker API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/docs"
    OPENAPI_SWAGGER_UI_PATH = ""
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Optional site URL for email redirect on Supabase signup email confirmation
    SITE_URL = os.getenv("SITE_URL")
