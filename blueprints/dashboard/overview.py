from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time


overview_bp = Blueprint("overview", __name__, url_prefix="/dashboard/overview")
# ── OVERVIEW ──────────────────────────────────────────────

@overview_bp.route("/")
@project_required
def overview():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/overview.html", data=data)


@overview_bp.route("/save", methods=["POST"])
@project_required
def overview_save():
    username, pid = session["username"], session["project_id"]
    phases = [
        {"label": p, "state": request.form.get(f"phase_state_{p}", "todo")}
        for p in request.form.getlist("phase_label")
    ]
    _save(username, pid, {
        "project.name":       request.form.get("name", ""),
        "project.client":     request.form.get("client", ""),
        "project.pm":         request.form.get("pm", ""),
        "project.start":      request.form.get("start", ""),
        "project.end":        request.form.get("end", ""),
        "project.sprint_len": request.form.get("sprint_len", "2"),
        "project.goal":       request.form.get("goal", ""),
        "phases":             phases,
    })
    return redirect(url_for("overview.overview"))
