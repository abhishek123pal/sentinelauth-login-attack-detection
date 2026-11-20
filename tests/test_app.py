# from app import db
# from app.models import LoginEvent, SecurityAlert

# def test_health(client):
#     assert client.get("/health").status_code == 200

# def test_login_failure_is_logged(client, app):
#     response = client.post("/login", data={"username": "unknown", "password": "wrong"})
#     assert response.status_code == 401
#     with app.app_context():
#         assert LoginEvent.query.filter_by(status="FAILURE").count() == 1

# def test_admin_login_and_dashboard(client):
#     response = client.post("/login", data={"username": "admin", "password": "AdminPassword123!"})
#     assert response.status_code == 302
#     assert client.get("/admin").status_code == 200

# def test_non_admin_cannot_access_admin(client):
#     client.post("/register", data={"username": "normaluser", "password": "VeryStrongPassword123!"})
#     client.post("/login", data={"username": "normaluser", "password": "VeryStrongPassword123!"})
#     assert client.get("/admin").status_code == 403

# def test_bruteforce_creates_alert(client, app):
#     for _ in range(5):
#         client.post("/login", data={"username": "missing", "password": "wrong"})
#     with app.app_context():
#         alert = SecurityAlert.query.filter_by(alert_type="BRUTE_FORCE").first()
#         assert alert is not None


# from app import db
# from app.models import LoginEvent, SecurityAlert

# # ----------------------------------
# # 1. HEALTH CHECK
# # ----------------------------------


# def test_health(client):
#     response = client.get("/health")

#     assert response.status_code == 200
#     assert response.json["status"] == "ok"


# # ----------------------------------
# # 2. FAILED LOGIN LOGGING
# # ----------------------------------


# def test_login_failure_is_logged(client, app):
#     response = client.post("/login", data={"username": "unknown", "password": "wrong"})

#     assert response.status_code == 401

#     with app.app_context():
#         event = LoginEvent.query.filter_by(status="FAILURE").first()

#         assert event is not None
#         assert event.attempted_username == "unknown"


# # ----------------------------------
# # 3. ADMIN LOGIN
# # ----------------------------------


# def test_admin_login_and_dashboard(client):
#     response = client.post(
#         "/login", data={"username": "admin", "password": "AdminPassword123!"}
#     )

#     assert response.status_code == 302

#     dashboard = client.get("/admin")

#     assert dashboard.status_code == 200


# # ----------------------------------
# # 4. USER AUTHORIZATION
# # ----------------------------------


# def test_non_admin_cannot_access_admin(client):
#     client.post(
#         "/register",
#         data={"username": "normaluser", "password": "VeryStrongPassword123!"},
#     )

#     client.post(
#         "/login", data={"username": "normaluser", "password": "VeryStrongPassword123!"}
#     )

#     response = client.get("/admin")

#     assert response.status_code == 403


# # ----------------------------------
# # 5. BRUTE FORCE DETECTION
# # ----------------------------------


# def test_bruteforce_creates_alert(client, app):
#     for _ in range(5):
#         client.post("/login", data={"username": "missing", "password": "wrong"})

#     with app.app_context():
#         alert = SecurityAlert.query.filter_by(alert_type="BRUTE_FORCE").first()

#         assert alert is not None
#         assert alert.severity == "HIGH"


# # ----------------------------------
# # 6. PASSWORD SPRAYING DETECTION
# # ----------------------------------


# def test_password_spraying_creates_alert(client, app):
#     ip = "192.0.2.10"

#     for i in range(10):
#         client.post(
#             "/login",
#             data={"username": f"target_user_{i}", "password": "WrongPassword123!"},
#             environ_overrides={"REMOTE_ADDR": ip},
#         )

#     with app.app_context():
#         alert = SecurityAlert.query.filter_by(alert_type="PASSWORD_SPRAYING").first()

#         assert alert is not None
#         assert alert.severity == "HIGH"


# # ----------------------------------
# # 7. DISTRIBUTED TARGETING DETECTION
# # ----------------------------------


# def test_distributed_targeting_creates_alert(client, app):
#     target_username = "victim_account"

#     for i in range(1, 6):
#         ip = f"192.0.2.{i}"

#         client.post(
#             "/login",
#             data={"username": target_username, "password": "WrongPassword123!"},
#             environ_overrides={"REMOTE_ADDR": ip},
#         )

#     with app.app_context():
#         alert = SecurityAlert.query.filter_by(
#             alert_type="DISTRIBUTED_TARGETING"
#         ).first()

#         assert alert is not None
#         assert alert.severity == "MEDIUM"


# # ----------------------------------
# # 8. ALERT DEDUPLICATION
# # ----------------------------------


# def test_duplicate_alerts_are_prevented(client, app):
#     ip = "192.0.2.50"

#     for _ in range(8):
#         client.post(
#             "/login",
#             data={"username": "duplicate_test", "password": "wrong"},
#             environ_overrides={"REMOTE_ADDR": ip},
#         )

#     with app.app_context():
#         alerts = SecurityAlert.query.filter_by(
#             source_ip=ip, alert_type="BRUTE_FORCE", status="OPEN"
#         ).all()

#         assert len(alerts) == 1

import re

from app.models import LoginEvent, SecurityAlert


def get_csrf_token(client, path="/login"):
    response = client.get(path)

    assert response.status_code == 200

    html = response.get_data(as_text=True)

    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)

    assert match is not None, "CSRF token missing from form"

    return match.group(1)


def post_with_csrf(client, path, data, ip=None):
    token = get_csrf_token(client, path)

    payload = {**data, "csrf_token": token}

    options = {}

    if ip:
        options["environ_overrides"] = {"REMOTE_ADDR": ip}

    return client.post(path, data=payload, **options)


# 1. HEALTH CHECK


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "ok"


# 2. FAILED LOGIN LOGGING


def test_login_failure_is_logged(client, app):

    response = post_with_csrf(
        client, "/login", {"username": "unknown", "password": "wrong"}
    )

    assert response.status_code == 401

    with app.app_context():
        assert LoginEvent.query.filter_by(status="FAILURE").count() == 1


# 3. ADMIN LOGIN


def test_admin_login_and_dashboard(client):

    response = post_with_csrf(
        client, "/login", {"username": "admin", "password": "AdminPassword123!"}
    )

    assert response.status_code == 302
    assert client.get("/admin").status_code == 200


# 4. USER AUTHORIZATION


def test_non_admin_cannot_access_admin(client):

    response = post_with_csrf(
        client,
        "/register",
        {"username": "normaluser", "password": "VeryStrongPassword123!"},
    )

    assert response.status_code == 302

    post_with_csrf(
        client,
        "/login",
        {"username": "normaluser", "password": "VeryStrongPassword123!"},
    )

    assert client.get("/admin").status_code == 403


# 5. BRUTE FORCE DETECTION


def test_bruteforce_creates_alert(client, app):

    for _ in range(5):
        post_with_csrf(
            client,
            "/login",
            {"username": "missing", "password": "wrong"},
            ip="192.0.2.10",
        )

    with app.app_context():
        alert = SecurityAlert.query.filter_by(alert_type="BRUTE_FORCE").first()

        assert alert is not None
        assert alert.severity == "HIGH"


# 6. PASSWORD SPRAYING


def test_password_spraying_creates_alert(client, app):

    ip = "192.0.2.20"

    for i in range(10):
        post_with_csrf(
            client,
            "/login",
            {"username": f"target_user_{i}", "password": "WrongPassword123!"},
            ip=ip,
        )

    with app.app_context():
        alert = SecurityAlert.query.filter_by(alert_type="PASSWORD_SPRAYING").first()

        assert alert is not None
        assert alert.severity == "HIGH"


# 7. DISTRIBUTED TARGETING


def test_distributed_targeting_creates_alert(client, app):

    for i in range(1, 6):
        post_with_csrf(
            client,
            "/login",
            {"username": "victim_account", "password": "WrongPassword123!"},
            ip=f"192.0.2.{i}",
        )

    with app.app_context():
        alert = SecurityAlert.query.filter_by(
            alert_type="DISTRIBUTED_TARGETING"
        ).first()

        assert alert is not None
        assert alert.severity == "MEDIUM"


# 8. ALERT DEDUPLICATION


def test_duplicate_alerts_are_prevented(client, app):

    for _ in range(8):
        post_with_csrf(
            client,
            "/login",
            {"username": "duplicate_test", "password": "wrong"},
            ip="192.0.2.50",
        )

    with app.app_context():
        alerts = SecurityAlert.query.filter_by(
            source_ip="192.0.2.50", alert_type="BRUTE_FORCE", status="OPEN"
        ).all()

        assert len(alerts) == 1


# 9. CSRF PROTECTION


def test_login_rejects_missing_csrf_token(client, app):

    response = client.post("/login", data={"username": "unknown", "password": "wrong"})

    assert response.status_code == 400

    with app.app_context():
        assert LoginEvent.query.count() == 0


# 10. SECURITY HEADERS


def test_security_headers(client):

    response = client.get("/health")

    assert response.headers.get("X-Content-Type-Options") == "nosniff"

    assert response.headers.get("X-Frame-Options") == "DENY"

    assert response.headers.get("Content-Security-Policy") is not None
