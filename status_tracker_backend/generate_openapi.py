import json
import os
from app import create_app  # app factory

app = create_app()

with app.app_context():
    # flask-smorest stores the spec via app.extensions. Extract spec from the registered Api instance.
    api = next((ext for ext in app.extensions.get("flask-smorest", []) if hasattr(ext, "spec")), None)
    if api is None:
        raise RuntimeError("API spec not found. Ensure Api is initialized.")
    openapi_spec = api.spec.to_dict()

    output_dir = "interfaces"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "openapi.json")

    with open(output_path, "w") as f:
        json.dump(openapi_spec, f, indent=2)
