from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time


team_bp = Blueprint("team", __name__, url_prefix="/dashboard/team")
# ── TEAM ──────────────────────────────────────────────────

@team_bp.route("/")
@project_required
def team():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/team.html", data=data)


@team_bp.route("/add", methods=["POST"])
@project_required
def team_add():
    username, pid = session["username"], session["project_id"]
    data   = get_project(username, pid)
    member = {
        "id":   f"t_{int(time.time())}",
        "name": request.form.get("name", "").strip(),
        "role": request.form.get("role", "Developer"),
    }
    if member["name"]:
        team_list = data.get("team", [])
        team_list.append(member)
        _save(username, pid, {"team": team_list})
    return redirect(url_for("team.team"))


@team_bp.route("/delete/<member_id>", methods=["POST"])
@project_required
def team_delete(member_id):
    username, pid = session["username"], session["project_id"]
    data      = get_project(username, pid)
    team_list = [m for m in data.get("team", []) if m["id"] != member_id]
    _save(username, pid, {"team": team_list})

    return redirect(url_for("team.team"))

