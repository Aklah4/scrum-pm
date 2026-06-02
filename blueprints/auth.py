from flask import Blueprint, render_template, request, session, redirect, url_for
from db import users
from extensions import limiter
from email_validator import validate_email, EmailNotValidError
from datetime import datetime
import bcrypt

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")

        if not username or not email or not password:
            error = "All fields are required."
        else:
            try:
                email = validate_email(email, check_deliverability=True).normalized
            except EmailNotValidError as e:
                error = str(e)

        if not error:
            if len(password) < 8:
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
@limiter.limit("10 per minute")
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
