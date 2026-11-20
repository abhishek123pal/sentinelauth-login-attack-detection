import os

from dotenv import load_dotenv
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

load_dotenv()

db = SQLAlchemy()

limiter = Limiter(key_func=get_remote_address, default_limits=[])

csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///sentinelauth.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=(os.getenv("COOKIE_SECURE", "0") == "1"),
        PERMANENT_SESSION_LIFETIME=1800,
        WTF_CSRF_ENABLED=True,
        WTF_CSRF_TIME_LIMIT=3600,
        DEBUG=os.getenv("FLASK_DEBUG", "0") == "1",
        RATELIMIT_STORAGE_URI=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
    )

    # Test configuration overrides development configuration.
    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions.
    db.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)

    # Import models and routes.
    from app import models, routes  # noqa: F401

    # Initialize database and default admin.
    with app.app_context():
        db.create_all()
        create_default_admin()

    # Register application routes.
    from app.routes import register_routes

    register_routes(app)

    # Security response headers.
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=()"
        )

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        return response

    return app


def create_default_admin():
    from app.models import User
    from werkzeug.security import generate_password_hash

    username = os.getenv("ADMIN_USERNAME", "admin")
    password = os.getenv("ADMIN_PASSWORD", "ChangeThisAdminPassword123!")

    if not User.query.filter_by(username=username).first():
        db.session.add(
            User(
                username=username,
                password_hash=generate_password_hash(password),
                role="admin",
                is_active=True,
            )
        )
        db.session.commit()
