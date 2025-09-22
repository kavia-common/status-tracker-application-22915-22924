from flask import Flask
from flask_cors import CORS
from flask_smorest import Api
from .config import Config
from .extensions import db, migrate, ma, jwt
from .routes.health import blp as health_blp
from .routes.auth import blp as auth_blp
from .routes.users import blp as users_blp
from .routes.statuses import blp as statuses_blp


def create_app():
    """Application factory for Status Tracker backend."""
    app = Flask(__name__)
    app.url_map.strict_slashes = False

    # Load config
    app.config.from_object(Config)

    # CORS
    CORS(app, resources={r"/*": {"origins": app.config.get("CORS_ORIGINS", "*")}})

    # API docs
    app.config["API_TITLE"] = app.config.get("API_TITLE", "Status Tracker API")
    app.config["API_VERSION"] = app.config.get("API_VERSION", "v1")
    app.config["OPENAPI_VERSION"] = app.config.get("OPENAPI_VERSION", "3.0.3")
    app.config["OPENAPI_URL_PREFIX"] = app.config.get("OPENAPI_URL_PREFIX", "/docs")
    app.config["OPENAPI_SWAGGER_UI_PATH"] = app.config.get("OPENAPI_SWAGGER_UI_PATH", "")
    app.config["OPENAPI_SWAGGER_UI_URL"] = app.config.get("OPENAPI_SWAGGER_UI_URL", "https://cdn.jsdelivr.net/npm/swagger-ui-dist/")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    jwt.init_app(app)

    # Smorest API
    api = Api(app, spec_kwargs={"info": {"description": "REST API for authentication, user management, and status CRUD."}})
    api.register_blueprint(health_blp)
    api.register_blueprint(auth_blp)
    api.register_blueprint(users_blp)
    api.register_blueprint(statuses_blp)

    # OpenAPI tags order
    api.spec.tags = [
        {"name": "Healt Check", "description": "Health check route"},
        {"name": "Auth", "description": "Authentication routes for login, logout, and token refresh."},
        {"name": "Users", "description": "User management endpoints."},
        {"name": "Statuses", "description": "CRUD for status items."},
    ]

    # CLI commands
    from . import cli as cli_module  # noqa: F401
    try:
        from .cli import init_db_command
        app.cli.add_command(init_db_command)
    except Exception:
        pass

    return app


# Expose app and api for existing scripts
app = create_app()
api = next((ext for ext in app.extensions.get("flask-smorest", []) if isinstance(ext, Api)), None)
