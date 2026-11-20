import pytest

from app import create_app, db
from app.models import User
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SECRET_KEY": "test-secret-key",
            "RATELIMIT_ENABLED": False,
            "WTF_CSRF_ENABLED": True,
        }
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

        admin = User(
            username="admin",
            password_hash=generate_password_hash("AdminPassword123!"),
            role="admin",
            is_active=True,
        )

        db.session.add(admin)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def create_login_event(app):
    def _create(ip, username, status="FAILURE"):
        from app.security import record_login_event

        with app.app_context():
            return record_login_event(username=username, ip=ip, status=status)

    return _create
