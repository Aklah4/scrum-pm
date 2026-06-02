from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _save
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time

risks_bp = Blueprint("risks", __name__, url_prefix="/dashboard/risks")
# ── RISKS ─────────────────────────────────────────────────

@risks_bp.route("/")
@project_required
def risks():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/risks.html", data=data)


@risks_bp.route("/add", methods=["POST"])
@project_required
def risks_add():
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    risk = {
        "id":         f"r_{int(time.time())}",
        "title":      request.form.get("title", "").strip(),
        "level":      request.form.get("level", "med"),
        "mitigation": request.form.get("mitigation", "").strip(),
    }
    if risk["title"]:
        risk_list = data.get("risks", [])
        risk_list.append(risk)
        _save(username, pid, {"risks": risk_list})
    return redirect(url_for("risks.risks"))


@risks_bp.route("/edit/<risk_id>", methods=["POST"])
@project_required
def risks_edit(risk_id):
    username, pid = session["username"], session["project_id"]
    data      = get_project(username, pid)
    risk_list = data.get("risks", [])
    for r in risk_list:
        if r["id"] == risk_id:
            r["title"]      = request.form.get("title", r["title"]).strip()
            r["level"]      = request.form.get("level", r["level"])
            r["mitigation"] = request.form.get("mitigation", r.get("mitigation", "")).strip()
            break
    _save(username, pid, {"risks": risk_list})
    return redirect(url_for("risks.risks"))


@risks_bp.route("/delete/<risk_id>", methods=["POST"])
@project_required
def risks_delete(risk_id):
    username, pid = session["username"], session["project_id"]
    data      = get_project(username, pid)
    risk_list = [r for r in data.get("risks", []) if r["id"] != risk_id]
    _save(username, pid, {"risks": risk_list})
    return redirect(url_for("risks.risks"))

