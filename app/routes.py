from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import render_template, request, redirect, url_for, flash, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from app import db, limiter
from app.models import User, LoginEvent, SecurityAlert
from app.security import record_login_event

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id") or session.get("role") != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper

def register_routes(app):
    @app.context_processor
    def inject_user():
        return {"current_user": session.get("username"), "current_role": session.get("role")}

    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard"))
        return redirect(url_for("login"))

    @app.route("/register", methods=["GET", "POST"])
    @limiter.limit("5 per hour", methods=["POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if len(username) < 3 or len(username) > 80 or len(password) < 12:
                flash("Use a username of 3–80 characters and a password of at least 12 characters.", "error")
                return render_template("register.html")
            if User.query.filter_by(username=username).first():
                flash("Registration could not be completed with those details.", "error")
                return render_template("register.html")
            user = User(username=username, password_hash=generate_password_hash(password), role="user")
            db.session.add(user)
            db.session.commit()
            flash("Account created. You can now sign in.", "success")
            return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    @limiter.limit("10 per minute", methods=["POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            ip = request.remote_addr or "unknown"
            user = User.query.filter_by(username=username).first()
            valid = bool(user and user.is_active and check_password_hash(user.password_hash, password))
            record_login_event(
                username or "(empty)", ip, "SUCCESS" if valid else "FAILURE",
                user.id if valid else None, request.headers.get("User-Agent", "")
            )
            if not valid:
                flash("Invalid username or password.", "error")
                return render_template("login.html"), 401
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role
            session.permanent = True
            return redirect(url_for("admin_dashboard" if user.role == "admin" else "dashboard"))
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        flash("You have been signed out.", "success")
        return redirect(url_for("login"))

    @app.route("/dashboard")
    def dashboard():
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return render_template("dashboard.html")

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        total = LoginEvent.query.count()
        failed = LoginEvent.query.filter_by(status="FAILURE").count()
        successful = LoginEvent.query.filter_by(status="SUCCESS").count()
        open_alerts = SecurityAlert.query.filter_by(status="OPEN").count()
        recent_events = LoginEvent.query.order_by(LoginEvent.created_at.desc()).limit(12).all()
        recent_alerts = SecurityAlert.query.order_by(SecurityAlert.created_at.desc()).limit(8).all()
        return render_template("admin.html", total=total, failed=failed,
                               successful=successful, open_alerts=open_alerts,
                               recent_events=recent_events, recent_alerts=recent_alerts)

    @app.route("/admin/events")
    @admin_required
    def events():
        page = max(request.args.get("page", 1, type=int), 1)
        pagination = LoginEvent.query.order_by(LoginEvent.created_at.desc()).paginate(
            page=page, per_page=30, error_out=False
        )
        return render_template("events.html", pagination=pagination)

    @app.route("/admin/alerts")
    @admin_required
    def alerts():
        records = SecurityAlert.query.order_by(SecurityAlert.created_at.desc()).limit(200).all()
        return render_template("alerts.html", alerts=records)

    @app.route("/admin/alerts/<int:alert_id>/resolve", methods=["POST"])
    @admin_required
    def resolve_alert(alert_id):
        alert = db.session.get(SecurityAlert, alert_id)
        if not alert:
            abort(404)
        alert.status = "RESOLVED"
        db.session.commit()
        flash("Alert marked as resolved.", "success")
        return redirect(url_for("alerts"))

    @app.route("/api/metrics")
    @admin_required
    def metrics():
        since = datetime.now(timezone.utc) - timedelta(days=7)
        rows = db.session.query(
            func.strftime("%Y-%m-%d", LoginEvent.created_at),
            LoginEvent.status, func.count(LoginEvent.id)
        ).filter(LoginEvent.created_at >= since).group_by(
            func.strftime("%Y-%m-%d", LoginEvent.created_at), LoginEvent.status
        ).all()
        labels = sorted({r[0] for r in rows if r[0]})
        success = {r[0]: r[2] for r in rows if r[1] == "SUCCESS"}
        failure = {r[0]: r[2] for r in rows if r[1] == "FAILURE"}
        return jsonify({
            "labels": labels,
            "success": [success.get(day, 0) for day in labels],
            "failure": [failure.get(day, 0) for day in labels]
        })

    @app.route("/health")
    def health():
        return jsonify({"status": "ok"})
