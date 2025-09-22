from flask_smorest import Blueprint
from flask.views import MethodView

# Keep tag name consistent with existing openapi file but fix internal blueprint identifier
blp = Blueprint("Healt Check", "health", url_prefix="/", description="Health check route")


@blp.route("/")
class HealthCheck(MethodView):
    """Health check endpoint."""
    # PUBLIC_INTERFACE
    def get(self):
        """Return a simple health status."""
        return {"message": "Healthy"}
