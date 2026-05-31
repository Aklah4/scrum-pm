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
    """Requires both a logged-in user AND an active project in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("auth.login"))
        if "project_id" not in session:
            return redirect(url_for("dashboard.projects_home"))
        return f(*args, **kwargs)
    return decorated
