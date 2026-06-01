from flask import Blueprint, render_template, request, session, redirect, url_for
from db import users
from datetime import datetime
import bcrypt
import re
import dns.resolver

auth_bp = Blueprint("auth", __name__)

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def _email_domain_valid(email):
    """Return True if the email's domain has MX records (can receive mail)."""
    try:
        domain = email.split('@')[1]
        dns.resolver.resolve(domain, 'MX', lifetime=5)
        return True
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return False
    except Exception:
        return True  # DNS unavailable — fail open rather than block all registrations


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")

        if not username or not email or not password:
            error = "All fields are required."
        elif not _EMAIL_RE.match(email):
            error = "Please enter a valid email address."
        elif not _email_domain_valid(email):
            error = "That email domain doesn't exist. Please use a real email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords do not match."
        elif users.find_one({"username": username}):
            error = "Username already taken."
        elif users.find_one({"email": email}):
            error = "An account with that email already exists."
        else:
            users.insert_one({
                "username":      username,
                "email":         email,
                "password_hash": bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()),
                "created_at":    datetime.utcnow()
            })
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", error=error)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user     = users.find_one({"username": username})

        if not user or not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"]):
            error = "Invalid username or password."
        else:
            session["username"] = username
            # Always land on project picker — user chooses which project to open
            return redirect(url_for("dashboard.projects_home"))

    return render_template("auth/login.html", error=error)


@auth_bp.route("/logout")
def logout():
    session.clear()          # clears username, project_id, and anything else
    return redirect(url_for("auth.login"))
