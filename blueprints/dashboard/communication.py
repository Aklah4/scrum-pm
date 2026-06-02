from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time

comms_bp = Blueprint("comms", __name__, url_prefix="/dashboard/comms")
# ── COMMUNICATION PLAN ────────────────────────────────────

@comms_bp.route("/")
@project_required
def comms():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/comms.html", data=data)


@comms_bp.route("/add", methods=["POST"])
@project_required
def comms_add():
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    item = {
        "id":          f"cm_{int(time.time())}",
        "stakeholder": request.form.get("stakeholder", "").strip(),
        "type":        request.form.get("type", "").strip(),
        "frequency":   request.form.get("frequency", "").strip(),
        "owner":       request.form.get("owner", "").strip(),
        "notes":       request.form.get("notes", "").strip(),
    }
    if item["stakeholder"]:
        lst = data.get("comms", [])
        lst.append(item)
        _save(username, pid, {"comms": lst})
    return redirect(url_for("comms.comms"))


@comms_bp.route("/delete/<item_id>", methods=["POST"])
@project_required
def comms_delete(item_id):
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    lst  = [c for c in data.get("comms", []) if c["id"] != item_id]
    _save(username, pid, {"comms": lst})
    return redirect(url_for("comms.comms"))

