from flask import Blueprint, render_template, request
from db import contactus as contactus_col
from extensions import limiter
from datetime import datetime, timezone

contactus_bp = Blueprint("contactus", __name__)


@contactus_bp.route("/contact", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def contact():
    success = False
    error   = None

    if request.method == "POST":
        name    = request.form.get("name", "").strip()
        email   = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            error = "All fields are required."
        else:
            contactus_col.insert_one({
                "name":       name,
                "email":      email,
                "message":    message,
                "created_at": datetime.now(timezone.utc),
            })
            success = True

    return render_template("contactus.html", success=success, error=error)
