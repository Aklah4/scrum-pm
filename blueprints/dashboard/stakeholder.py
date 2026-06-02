from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time

stakeholder_bp = Blueprint("stakeholder", __name__, url_prefix="/dashboard/stakeholders")
# ── STAKEHOLDERS ──────────────────────────────────────────

@stakeholder_bp.route("/")
@project_required
def stakeholders():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/stakeholders.html", data=data)


@stakeholder_bp.route("/add", methods=["POST"])
@project_required
def stakeholders_add():
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    item = {
        "id":        f"sk_{int(time.time())}",
        "name":      request.form.get("name", "").strip(),
        "org":       request.form.get("org", "").strip(),
        "title":     request.form.get("title", "").strip(),
        "interest":  request.form.get("interest", "med"),
        "influence": request.form.get("influence", "med"),
        "contact":   request.form.get("contact", "").strip(),
        "notes":     request.form.get("notes", "").strip(),
    }
    if item["name"]:
        lst = data.get("stakeholders", [])
        lst.append(item)
        _save(username, pid, {"stakeholders": lst})
    return redirect(url_for("stakeholder.stakeholders"))


@stakeholder_bp.route("/edit/<item_id>", methods=["POST"])
@project_required
def stakeholders_edit(item_id):
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    lst  = data.get("stakeholders", [])
    for s in lst:
        if s["id"] == item_id:
            s["name"]      = request.form.get("name",      s["name"]).strip()
            s["org"]       = request.form.get("org",       s.get("org", "")).strip()
            s["title"]     = request.form.get("title",     s.get("title", "")).strip()
            s["interest"]  = request.form.get("interest",  s.get("interest", "med"))
            s["influence"] = request.form.get("influence", s.get("influence", "med"))
            s["contact"]   = request.form.get("contact",   s.get("contact", "")).strip()
            s["notes"]     = request.form.get("notes",     s.get("notes", "")).strip()
            break
    _save(username, pid, {"stakeholders": lst})
    return redirect(url_for("stakeholder.stakeholders"))


@stakeholder_bp.route("/delete/<item_id>", methods=["POST"])
@project_required
def stakeholders_delete(item_id):
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    lst  = [s for s in data.get("stakeholders", []) if s["id"] != item_id]
    _save(username, pid, {"stakeholders": lst})
    return redirect(url_for("stakeholder.stakeholders"))

