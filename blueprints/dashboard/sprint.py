from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time

sprint_bp = Blueprint("sprint", __name__, url_prefix="/dashboard/sprint")
# ── SPRINTS ───────────────────────────────────────────────

@sprint_bp.route("/sprints/add", methods=["POST"])
@project_required
def sprints_add():
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    sprint = {
        "id":         f"sp_{int(time.time())}",
        "name":       request.form.get("name", "").strip(),
        "start_date": request.form.get("start_date", "").strip(),
        "end_date":   request.form.get("end_date", "").strip(),
        "goal":       request.form.get("goal", "").strip(),
    }
    if sprint["name"]:
        sprints_list = data.get("sprints", [])
        sprints_list.append(sprint)
        _save(username, pid, {"sprints": sprints_list})
    return redirect(url_for("sprint.sprint_config"))


@sprint_bp.route("/sprints/delete/<sprint_id>", methods=["POST"])
@project_required
def sprints_delete(sprint_id):
    username, pid = session["username"], session["project_id"]
    data         = get_project(username, pid)
    sprints_list = [s for s in data.get("sprints", []) if s["id"] != sprint_id]
    stories      = data.get("stories", [])
    for s in stories:
        if s.get("sprint_id") == sprint_id:
            s["sprint_id"] = ""
    _save(username, pid, {"sprints": sprints_list, "stories": stories})
    return redirect(url_for("sprint.sprint_config"))


@sprint_bp.route("/sprint")
@project_required
def sprint():
    username, pid = session["username"], session["project_id"]
    data         = get_project(username, pid)
    sprints_list = data.get("sprints", [])
    sprint_id    = request.args.get("sprint", "")

    if not sprint_id and sprints_list:
        sprint_id = sprints_list[0]["id"]

    current_sprint = next((s for s in sprints_list if s["id"] == sprint_id), None)
    all_stories    = data.get("stories", [])
    sprint_stories = [s for s in all_stories if s.get("sprint_id") == sprint_id] if sprint_id else []

    kanban = {
        "todo":   [s for s in sprint_stories if s.get("status", "todo") == "todo"],
        "inprog": [s for s in sprint_stories if s.get("status") == "inprog"],
        "done":   [s for s in sprint_stories if s.get("status") == "done"],
    }

    return render_template(
        "dashboard/sprint.html",
        data=data,
        sprints=sprints_list,
        current_sprint=current_sprint,
        sprint_id=sprint_id,
        kanban=kanban,
    )


@sprint_bp.route("/sprint/story/move/<story_id>", methods=["POST"])
@project_required
def sprint_story_move(story_id):
    username, pid = session["username"], session["project_id"]
    data    = get_project(username, pid)
    stories = data.get("stories", [])
    order   = ["todo", "inprog", "done"]
    for s in stories:
        if s["id"] == story_id:
            idx       = order.index(s.get("status", "todo")) if s.get("status", "todo") in order else 0
            s["status"] = order[min(idx + 1, 2)]
            break
    _save(username, pid, {"stories": stories})
    return redirect(url_for("sprint.sprint", sprint=request.form.get("sprint_id", "")))


@sprint_bp.route("/sprint/story/back/<story_id>", methods=["POST"])
@project_required
def sprint_story_back(story_id):
    username, pid = session["username"], session["project_id"]
    data    = get_project(username, pid)
    stories = data.get("stories", [])
    order   = ["todo", "inprog", "done"]
    for s in stories:
        if s["id"] == story_id:
            idx       = order.index(s.get("status", "todo")) if s.get("status", "todo") in order else 0
            s["status"] = order[max(idx - 1, 0)]
            break
    _save(username, pid, {"stories": stories})
    return redirect(url_for("sprint.sprint", sprint=request.form.get("sprint_id", "")))


@sprint_bp.route("/sprint-config")
@project_required
def sprint_config():
    data         = get_project(session["username"], session["project_id"])
    sprints_list = data.get("sprints", [])
    return render_template("dashboard/sprint_config.html", data=data, sprints=sprints_list)


@sprint_bp.route("/sprint-config/save", methods=["POST"])
@project_required
def sprint_config_save():
    username, pid = session["username"], session["project_id"]
    cfg = {
        "name":       request.form.get("name", "Sprint 1").strip(),
        "goal":       request.form.get("goal", "").strip(),
        "start_date": request.form.get("start_date", "").strip(),
        "end_date":   request.form.get("end_date", "").strip(),
        "length":     request.form.get("length", "2"),
        "velocity":   request.form.get("velocity", "").strip(),
        "capacity":   request.form.get("capacity", "").strip(),
    }
    dor_texts = request.form.getlist("dor_text")
    existing  = request.form.getlist("dor_existing")
    dor = [{"text": t.strip()} for t in dor_texts if t.strip()]
    dor += [{"text": t.strip()} for t in existing if t.strip()]
    _save(username, pid, {"sprint_cfg": cfg, "dor": dor})
    return redirect(url_for("sprint.sprint_config"))


@sprint_bp.route("/sprint-config/dor/delete/<int:idx>", methods=["POST"])
@project_required
def dor_delete(idx):
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    dor  = data.get("dor", [])
    if 0 <= idx < len(dor):
        del dor[idx]
        _save(username, pid, {"dor": dor})
    return redirect(url_for("sprint.sprint_config"))

