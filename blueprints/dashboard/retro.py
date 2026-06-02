from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time

retro_bp = Blueprint("retro", __name__, url_prefix="/dashboard/retro")
# ── RETRO ─────────────────────────────────────────────────

@retro_bp.route("/")
@project_required
def retro():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/retro.html", data=data)


@retro_bp.route("/add/<col>", methods=["POST"])
@project_required
def retro_add(col):
    if col not in ["went", "improve", "action"]:
        return redirect(url_for("retro.retro"))
    username, pid = session["username"], session["project_id"]
    data  = get_project(username, pid)
    item  = {"id": f"re_{int(time.time())}", "text": request.form.get("text", "").strip()}
    if item["text"]:
        retro = data.get("retro", {"went": [], "improve": [], "action": []})
        retro[col].append(item)
        _save(username, pid, {"retro": retro})
    return redirect(url_for("retro.retro"))


@retro_bp.route("/delete/<col>/<item_id>", methods=["POST"])
@project_required
def retro_delete(col, item_id):
    if col not in ["went", "improve", "action"]:
        return redirect(url_for("retro.retro"))
    username, pid = session["username"], session["project_id"]
    data  = get_project(username, pid)
    retro = data.get("retro", {"went": [], "improve": [], "action": []})
    retro[col] = [i for i in retro[col] if i["id"] != item_id]
    _save(username, pid, {"retro": retro})
    return redirect(url_for("retro.retro"))

