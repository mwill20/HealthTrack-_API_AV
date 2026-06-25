"""
HealthTrack API
A patient vitals tracking backend for clinics.
"""
import os

from flask import Flask

from .health import health_bp
from .routes import vitals_bp, patients_bp, alerts_bp


def create_app():
    app = Flask(__name__)
    # Pull the signing key from the environment; fall back to a dev value so
    # local runs work, but production must supply SECRET_KEY (see .env.example).
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
    app.register_blueprint(health_bp)
    app.register_blueprint(vitals_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(alerts_bp)
    return app
