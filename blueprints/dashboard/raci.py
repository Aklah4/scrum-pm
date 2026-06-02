from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time

raci_bp = Blueprint("raci", __name__, url_prefix="/dashboard/raci")
# ── ROLES & RESPONSIBILITY ────────────────────────────────

@raci_bp.route("/")
@project_required
def raci():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/raci.html", data=data)


@raci_bp.route("/add", methods=["POST"])
@project_required
def raci_add():
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    item = {
        "id":          f"rc_{int(time.time())}",
        "activity":    request.form.get("activity", "").strip(),
        "responsible": request.form.get("responsible", "").strip(),
        "accountable": request.form.get("accountable", "").strip(),
        "consulted":   request.form.get("consulted", "").strip(),
        "informed":    request.form.get("informed", "").strip(),
    }
    if item["activity"]:
        lst = data.get("raci", [])
        lst.append(item)
        _save(username, pid, {"raci": lst})
    return redirect(url_for("raci.raci"))


@raci_bp.route("/delete/<item_id>", methods=["POST"])
@project_required
def raci_delete(item_id):
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    lst  = [r for r in data.get("raci", []) if r["id"] != item_id]
    _save(username, pid, {"raci": lst})
    return redirect(url_for("raci.raci"))
