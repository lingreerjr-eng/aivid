from flask import Flask

from .config import load_settings
from .views import register_routes


def create_app() -> Flask:
    """Application factory for the AI video generator web app."""
    app = Flask(__name__)
    settings = load_settings()
    app.config["APP_SETTINGS"] = settings

    register_routes(app)

    return app


__all__ = ["create_app"]
