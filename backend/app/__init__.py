"""
CycloneAI backend application factory.

NOTE ON FRAMEWORK: the original brief specifies FastAPI. This build
environment has no internet access and `fastapi`/`uvicorn` are not
preinstalled, so Flask (which IS available) is used instead, with the same
route layout and JSON response shapes. To migrate to FastAPI on a machine
with internet access: `pip install fastapi uvicorn[standard]`, wrap each
route function below in an `APIRouter`, and replace `jsonify`/`request` with
Pydantic response/request models -- the service layer underneath
(`app/services/*`) does not need to change at all.
"""
from __future__ import annotations

import os

from flask import Flask


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DEMO_MODE=os.environ.get("DEMO_MODE", "true").lower() == "true",
        APP_ENV=os.environ.get("APP_ENV", "development"),
        SATELLITE_PROVIDER=os.environ.get("SATELLITE_PROVIDER", "demo"),
    )
    if config:
        app.config.update(config)

    # Minimal CORS handling (no external dependency needed) so the static
    # frontend can call this API from a different local port/origin.
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        return response

    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok", "demo_mode": app.config["DEMO_MODE"]}

    return app
