from datetime import datetime, timedelta, timezone
from sqlalchemy import func, distinct
from app import db
from app.models import LoginEvent, SecurityAlert

def record_login_event(username, ip, status, user_id=None, user_agent=""):
    event = LoginEvent(
        attempted_username=username[:80],
        user_id=user_id,
        source_ip=ip[:45],
        status=status,
        user_agent=user_agent[:255]
    )
    db.session.add(event)
    db.session.commit()
    if status == "FAILURE":
        detect_attacks(ip, username)
    return event

def create_alert(ip, alert_type, severity, description):
    existing = SecurityAlert.query.filter_by(
        source_ip=ip, alert_type=alert_type, status="OPEN"
    ).first()
    if existing:
        return existing
    alert = SecurityAlert(
        source_ip=ip,
        alert_type=alert_type,
        severity=severity,
        description=description
    )
    db.session.add(alert)
    db.session.commit()
    return alert

def detect_attacks(ip, username):
    now = datetime.now(timezone.utc)
    five_min = now - timedelta(minutes=5)
    ten_min = now - timedelta(minutes=10)

    failures = LoginEvent.query.filter(
        LoginEvent.source_ip == ip,
        LoginEvent.status == "FAILURE",
        LoginEvent.created_at >= five_min
    ).count()
    if failures >= 5:
        create_alert(ip, "BRUTE_FORCE", "HIGH",
                     f"{failures} failed login attempts from this IP in 5 minutes.")

    distinct_users = db.session.query(
        func.count(distinct(LoginEvent.attempted_username))
    ).filter(
        LoginEvent.source_ip == ip,
        LoginEvent.status == "FAILURE",
        LoginEvent.created_at >= ten_min
    ).scalar() or 0
    if distinct_users >= 10:
        create_alert(ip, "PASSWORD_SPRAYING", "HIGH",
                     f"This IP attempted authentication against {distinct_users} different usernames in 10 minutes.")

    distinct_ips = db.session.query(
        func.count(distinct(LoginEvent.source_ip))
    ).filter(
        LoginEvent.attempted_username == username,
        LoginEvent.status == "FAILURE",
        LoginEvent.created_at >= ten_min
    ).scalar() or 0
    if distinct_ips >= 5:
        create_alert(ip, "DISTRIBUTED_TARGETING", "MEDIUM",
                     f"{distinct_ips} different IP addresses targeted the same username in 10 minutes.")
