from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from db import users
from extensions import limiter, mail, serializer
from email_validator import validate_email, EmailNotValidError
from itsdangerous import SignatureExpired, BadSignature
from flask_mail import Message
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



# ── 1. Forgot Password (enter your email) ──────────────────
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user  = users.find_one({"email": email})

        if user:
            token     = serializer.dumps(email, salt="password-reset")
            reset_url = url_for("auth.reset_password", token=token, _external=True)

            msg      = Message(
                subject="Reset your ScrumPM password",
                recipients=[email]
            )
            msg.body = (
                f"Hi,\n\n"
                f"You requested a password reset for your ScrumPM account.\n\n"
                f"Click the link below to reset your password (expires in 30 minutes):\n\n"
                f"{reset_url}\n\n"
                f"If you didn't request this, ignore this email — your password won't change.\n\n"
                f"The ScrumPM Team"
            )
            try:
                mail.send(msg)
            except Exception as e:
                from flask import current_app
                current_app.logger.error(f"Password reset email failed: {e}")
                flash(f"Could not send email: {e}", "error")
                return render_template("auth/forgot_password.html")

        flash("If that email is registered, you'll receive a reset link shortly.", "info")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


# ── 2. Reset Password (click link from email) ──────────────
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset", max_age=1800)  # 30 min
    except SignatureExpired:
        flash("That reset link has expired. Please request a new one.", "error")
        return redirect(url_for("auth.forgot_password"))
    except BadSignature:
        flash("Invalid reset link.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password  = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        if password != password2:
            flash("Passwords do not match.", "error")
            return redirect(request.url)

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(request.url)

        hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        users.update_one(
            {"email": email},
            {"$set": {"password_hash": hashed_pw}}
        )

        flash("Password reset successful! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)