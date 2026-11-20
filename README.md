# SentinelAuth — Login Attack Detection System

A defensive authentication monitoring demo built with Flask, SQLite, SQLAlchemy and responsive HTML/CSS/JavaScript.

## Features
- User registration and session-based login
- Werkzeug password hashing
- Login success/failure audit events
- Brute-force detection: 5 failures from one IP in 5 minutes
- Password spraying detection: 10 distinct usernames from one IP in 10 minutes
- Distributed targeting detection: 5 distinct IPs targeting one username in 10 minutes
- Alert deduplication and admin resolution workflow
- Admin dashboard with seven-day login chart
- Role-protected event and alert pages
- Flask-Limiter request throttling
- Pytest starter suite and Docker deployment

## Requirements
Python 3.10+ (recommended 3.12).

## Run locally (Windows PowerShell)
```powershell
cd sentinelauth
py -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```
Edit `.env`. Set a unique `SECRET_KEY` and change the admin password before running.

```powershell
python run.py
```
Open http://127.0.0.1:5000

## Default admin configuration
The values in `.env.example` are demonstration placeholders:
- Username: `admin`
- Password: `ChangeThisAdminPassword123!`

Change the password before first use. The admin account is created only if it does not already exist. If you change the environment password after the account has been created, it will not reset the existing account password.

## Test
```bash
pytest -q
```

## Docker
```bash
cp .env.example .env
# Edit .env and set strong secrets
docker compose up --build -d
```
Open http://localhost:5000

## Important production hardening
This is a portfolio MVP, not a security-audited identity platform. Before public production use:
1. Use PostgreSQL and managed backups.
2. Use HTTPS and secure cookie settings (`COOKIE_SECURE=1`).
3. Add CSRF protection to all form actions and configure trusted host/proxy handling.
4. Use Redis-backed rate limiting for multi-worker/multi-instance deployments.
5. Move detection to a background queue and make alert deduplication atomic.
6. Add password reset, MFA, email verification, session revocation and account lifecycle flows.
7. Avoid exposing raw IPs/user agents to unauthorized users; define retention and privacy policies.
8. Add CSP and other security headers, dependency scanning and logging/monitoring.
9. Configure admin credentials through a secret manager, not committed files.

The detection thresholds are demonstration settings and should be tuned against real traffic to manage false positives.
