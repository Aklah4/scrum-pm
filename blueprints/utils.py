from functools import wraps
from flask import session, redirect, url_for


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def project_required(f):
    """Requires a logged-in user AND an active project that belongs to them."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("auth.login"))
        if "project_id" not in session:
            return redirect(url_for("dashboard.projects_home"))

        # Verify the project actually belongs to this user
        from db import projects as proj_col
        doc = proj_col.find_one(
            {"username": session["username"], "project_id": session["project_id"]},
            {"_id": 1}
        )
        if not doc:
            session.pop("project_id", None)
            return redirect(url_for("dashboard.projects_home"))

        return f(*args, **kwargs)
    return decorated
