from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time


def _safe_next(next_url, fallback):
    """Only follow next= if it is a relative path (prevents open redirect)."""
    if next_url:
        p = urlparse(next_url)
        if not p.scheme and not p.netloc:
            return next_url
    return fallback

dashboard_bp = Blueprint("dashboard", __name__)


def _save(username, pid, fields):
    """Update a single project document identified by username + project_id."""
    projects.update_one(
        {"username": username, "project_id": pid},
        {"$set": fields}
    )


# ── PROJECT MANAGEMENT ────────────────────────────────────

@dashboard_bp.route("/projects")
@login_required
def projects_home():
    session.pop("project_id", None)
    username = session["username"]
    all_docs = list(projects.find({"username": username}))

    # Migrate any legacy document that has no project_id
    for doc in all_docs:
        if not doc.get("project_id"):
            pid = f"proj_{int(time.time())}"
            projects.update_one(
                {"_id": doc["_id"]},
                {"$set": {"project_id": pid}}
            )
            doc["project_id"] = pid   # patch in-memory so template sees it

    return render_template("dashboard/projects.html", projects=all_docs)


@dashboard_bp.route("/projects/create", methods=["POST"])
@login_required
def projects_create():
    username     = session["username"]
    project_name = request.form.get("project_name", "").strip() or "Untitled Project"
    pm           = request.form.get("pm", "").strip()
    project_id   = f"proj_{int(time.time())}"

    # Creates the document with defaults
    get_project(username, project_id)

    # Immediately set the display name and PM
    _save(username, project_id, {
        "project.name": project_name,
        "project.pm":   pm or username,
    })

    session["project_id"] = project_id
    return redirect(url_for("overview.overview"))


@dashboard_bp.route("/projects/switch/<project_id>", methods=["POST"])
@login_required
def projects_switch(project_id):
    username = session["username"]
    doc = projects.find_one({"username": username, "project_id": project_id})
    if not doc:
        # project_id not found — go back to the list so the user can try again
        return redirect(url_for("dashboard.projects_home"))
    session["project_id"] = project_id
    return redirect(url_for("overview.overview"))


@dashboard_bp.route("/projects/delete/<project_id>", methods=["POST"])
@login_required
def projects_delete(project_id):
    username = session["username"]
    doc = projects.find_one({"username": username, "project_id": project_id})
    if doc:
        projects.delete_one({"username": username, "project_id": project_id})
        if session.get("project_id") == project_id:
            session.pop("project_id", None)
    return redirect(url_for("dashboard.projects_home"))


@dashboard_bp.route("/projects/exit")
@login_required
def projects_exit():
    session.pop("project_id", None)
    return redirect(url_for("dashboard.projects_home"))



