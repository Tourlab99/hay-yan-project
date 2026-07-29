"""
Hayqyan Travel - backend
=========================
Serves the static site (index.html, tours.html, about.html, contact.html,
style.css, script.js, Assets/) and stores every contact-form submission
and newsletter signup in a SQLite database, so the site owner can see
exactly who tried to reach them and about which tour.

Local run:
    pip install -r requirements.txt
    python app.py

Then open:
    http://localhost:5000            -> the website
    http://localhost:5000/admin      -> submissions list (password protected)

Production (Render, gunicorn, etc.):
    gunicorn app:app

Environment variables:
    ADMIN_USERNAME   admin panel login (default: admin)
    ADMIN_PASSWORD   admin panel password (default: changeme — CHANGE THIS)
    DATABASE_PATH    where to store submissions.db. Point this at a
                     mounted persistent disk on Render (e.g. /data/submissions.db)
                     or the database is wiped on every redeploy/restart.
"""

import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, request, jsonify, g, send_from_directory, Response, render_template_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SITE_DIR = os.path.join(os.path.dirname(BASE_DIR), "site")
DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "submissions.db"))

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")

app = Flask(__name__, static_folder=None)


# ---------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contact_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            message TEXT,
            interest TEXT,
            ip_address TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS newsletter_signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            page TEXT,
            ip_address TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------
# Admin auth (simple HTTP Basic Auth)
# ---------------------------------------------------------------------

def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                "Մուտք սահմանափակված է — խնդրում ենք մուտքագրել գործակալի տվյալները:",
                401,
                {"WWW-Authenticate": 'Basic realm="Hayqyan Travel Admin"'},
            )
        return f(*args, **kwargs)

    return decorated


# ---------------------------------------------------------------------
# API endpoints used by script.js
# ---------------------------------------------------------------------

@app.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()
    interest = (data.get("interest") or "").strip() or None

    if not name or not email:
        return jsonify({"error": "name and email are required"}), 400

    db = get_db()
    db.execute(
        """INSERT INTO contact_submissions (name, email, message, interest, ip_address, created_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, email, message, interest, request.remote_addr, datetime.utcnow().isoformat()),
    )
    db.commit()
    return jsonify({"status": "ok"}), 201


@app.route("/api/newsletter", methods=["POST"])
def api_newsletter():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    page = (data.get("page") or "").strip() or None

    if not email:
        return jsonify({"error": "email is required"}), 400

    db = get_db()
    db.execute(
        """INSERT INTO newsletter_signups (email, page, ip_address, created_at)
           VALUES (?, ?, ?, ?)""",
        (email, page, request.remote_addr, datetime.utcnow().isoformat()),
    )
    db.commit()
    return jsonify({"status": "ok"}), 201


# ---------------------------------------------------------------------
# Admin view — see who has tried to contact you
# ---------------------------------------------------------------------

ADMIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="hy">
<head>
<meta charset="UTF-8">
<title>Հաղորդագրություններ — Hayqyan Travel Admin</title>
<style>
  body { font-family: -apple-system, Arial, sans-serif; background: #F4F6F8; color: #17242C; margin: 0; padding: 32px; }
  h1 { color: #1B5FA8; }
  h2 { color: #1B5FA8; margin-top: 40px; }
  table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
  th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid #E4DACD; font-size: 14px; vertical-align: top; }
  th { background: #1B5FA8; color: #fff; font-weight: 600; }
  tr:last-child td { border-bottom: none; }
  .empty { color: #55666E; padding: 16px; }
  .badge { display: inline-block; background: #FFE9D2; color: #D9660A; border-radius: 100px; padding: 2px 10px; font-size: 12px; font-weight: 600; }
</style>
</head>
<body>
  <h1>Hayqyan Travel — Ովքե՞ր են փորձել կապվել</h1>

  <h2>Կապի ձևից ուղարկված հաղորդագրություններ ({{ contacts|length }})</h2>
  {% if contacts %}
  <table>
    <tr><th>Ամսաթիվ (UTC)</th><th>Անուն</th><th>Էլ. փոստ</th><th>Հետաքրքրված ուղևորություն</th><th>Հաղորդագրություն</th><th>IP</th></tr>
    {% for c in contacts %}
    <tr>
      <td>{{ c.created_at }}</td>
      <td>{{ c.name }}</td>
      <td>{{ c.email }}</td>
      <td>{% if c.interest %}<span class="badge">{{ c.interest }}</span>{% else %}—{% endif %}</td>
      <td>{{ c.message or "—" }}</td>
      <td>{{ c.ip_address }}</td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <p class="empty">Դեռ ոչ մի հաղորդագրություն չկա:</p>
  {% endif %}

  <h2>Նորությունների բաժանորդագրություններ ({{ newsletter|length }})</h2>
  {% if newsletter %}
  <table>
    <tr><th>Ամսաթիվ (UTC)</th><th>Էլ. փոստ</th><th>Էջ</th><th>IP</th></tr>
    {% for n in newsletter %}
    <tr>
      <td>{{ n.created_at }}</td>
      <td>{{ n.email }}</td>
      <td>{{ n.page or "—" }}</td>
      <td>{{ n.ip_address }}</td>
    </tr>
    {% endfor %}
  </table>
  {% else %}
  <p class="empty">Դեռ ոչ մի բաժանորդագրություն չկա:</p>
  {% endif %}
</body>
</html>
"""


@app.route("/admin")
@requires_auth
def admin():
    db = get_db()
    contacts = db.execute(
        "SELECT * FROM contact_submissions ORDER BY created_at DESC"
    ).fetchall()
    newsletter = db.execute(
        "SELECT * FROM newsletter_signups ORDER BY created_at DESC"
    ).fetchall()
    return render_template_string(ADMIN_TEMPLATE, contacts=contacts, newsletter=newsletter)


# ---------------------------------------------------------------------
# Static site
# ---------------------------------------------------------------------

@app.route("/")
def home():
    return send_from_directory(SITE_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(SITE_DIR, filename)


# Create tables on import — runs whether started via `python app.py`
# (dev server) or `gunicorn app:app` (production, e.g. Render).
init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
