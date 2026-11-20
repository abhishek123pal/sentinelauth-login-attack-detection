from datetime import datetime, timezone
from app import db

def utcnow():
    return datetime.now(timezone.utc)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

class LoginEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempted_username = db.Column(db.String(80), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    source_ip = db.Column(db.String(45), nullable=False, index=True)
    status = db.Column(db.String(12), nullable=False, index=True)
    user_agent = db.Column(db.String(255), default="")
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)

class SecurityAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_ip = db.Column(db.String(45), nullable=False, index=True)
    alert_type = db.Column(db.String(40), nullable=False)
    severity = db.Column(db.String(12), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="OPEN", index=True)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False, index=True)
