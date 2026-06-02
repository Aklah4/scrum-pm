from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time

dod_bp = Blueprint("dod", __name__, url_prefix="/dashboard/dod")

# ── DEFINITION OF DONE ────────────────────────────────────

@dod_bp.route("/")
@project_required
def dod():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/dod.html", data=data)


@dod_bp.route("/save", methods=["POST"])
@project_required
def dod_save():
    username, pid = session["username"], session["project_id"]
    data     = get_project(username, pid)
    dod_list = data.get("dod", [])
    checked  = request.form.getlist("checked")
    for item in dod_list:
        item["done"] = item["text"] in checked
    _save(username, pid, {"dod": dod_list})
    return redirect(url_for("dod.dod"))


