from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.dashboard.projects import _safe_next, _save
from blueprints.dashboard.projects import _save
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time

backlog_bp = Blueprint("backlog", __name__, url_prefix="/dashboard/backlog")
# ── BACKLOG & STORIES ─────────────────────────────────────

@backlog_bp.route("/backlog")
@project_required
def backlog():
    username, pid = session["username"], session["project_id"]
    data          = get_project(username, pid)
    sprint_filter = request.args.get("sprint", "")
    sprints_list  = data.get("sprints", [])
    all_stories   = data.get("stories", [])

    sprint_counts = {}
    for s in all_stories:
        sid = s.get("sprint_id") or ""
        sprint_counts[sid] = sprint_counts.get(sid, 0) + 1

    sprint_map = {sp["id"]: sp["name"] for sp in sprints_list}

    if sprint_filter == "__none__":
        filtered = [s for s in all_stories if not s.get("sprint_id")]
    elif sprint_filter:
        filtered = [s for s in all_stories if s.get("sprint_id") == sprint_filter]
    else:
        filtered = all_stories

    return render_template(
        "dashboard/backlog.html",
        data=data,
        sprints=sprints_list,
        sprint_filter=sprint_filter,
        filtered_stories=filtered,
        sprint_counts=sprint_counts,
        sprint_map=sprint_map,
    )


@backlog_bp.route("/backlog/add", methods=["POST"])
@project_required
def backlog_add():
    username, pid = session["username"], session["project_id"]
    data  = get_project(username, pid)
    story = {
        "id":        f"s_{int(time.time())}",
        "title":     request.form.get("title", "").strip(),
        "priority":  request.form.get("priority", "med"),
        "pts":       int(request.form.get("pts") or 3),
        "sprint_id": request.form.get("sprint_id", "").strip(),
    }
    if story["title"]:
        stories = data.get("stories", [])
        stories.append(story)
        _save(username, pid, {"stories": stories})
    return redirect(url_for("backlog.backlog"))


@backlog_bp.route("/backlog/edit/<story_id>", methods=["POST"])
@project_required
def backlog_edit(story_id):
    username, pid = session["username"], session["project_id"]
    data    = get_project(username, pid)
    stories = data.get("stories", [])
    for s in stories:
        if s["id"] == story_id:
            s["title"]     = request.form.get("title", s["title"]).strip()
            s["priority"]  = request.form.get("priority", s["priority"])
            s["pts"]       = int(request.form.get("pts") or s.get("pts", 3))
            s["sprint_id"] = request.form.get("sprint_id", s.get("sprint_id", ""))
            break
    _save(username, pid, {"stories": stories})
    return redirect(url_for("backlog.backlog"))


@backlog_bp.route("/backlog/assign/<story_id>", methods=["POST"])
@project_required
def backlog_assign(story_id):
    username, pid = session["username"], session["project_id"]
    data    = get_project(username, pid)
    stories = data.get("stories", [])
    for s in stories:
        if s["id"] == story_id:
            s["sprint_id"] = request.form.get("sprint_id", "").strip()
            break
    _save(username, pid, {"stories": stories})
    return redirect(url_for("backlog.backlog"))


@backlog_bp.route("/backlog/delete/<story_id>", methods=["POST"])
@project_required
def backlog_delete(story_id):
    username, pid = session["username"], session["project_id"]
    data   = get_project(username, pid)
    stories = [s for s in data.get("stories", []) if s["id"] != story_id]
    _save(username, pid, {"stories": stories})
    return redirect(url_for("backlog.backlog"))


@backlog_bp.route("/story/<story_id>/task/add", methods=["POST"])
@project_required
def task_add(story_id):
    username, pid = session["username"], session["project_id"]
    data    = get_project(username, pid)
    stories = data.get("stories", [])
    for s in stories:
        if s["id"] == story_id:
            tasks = s.get("tasks", [])
            text  = request.form.get("text", "").strip()
            if text:
                tasks.append({"id": f"t_{int(time.time())}", "text": text, "done": False})
                s["tasks"] = tasks
            break
    _save(username, pid, {"stories": stories})
    return redirect(_safe_next(request.form.get("next"), url_for("backlog.backlog")))


@backlog_bp.route("/story/<story_id>/task/toggle/<task_id>", methods=["POST"])
@project_required
def task_toggle(story_id, task_id):
    username, pid = session["username"], session["project_id"]
    data    = get_project(username, pid)
    stories = data.get("stories", [])
    for s in stories:
        if s["id"] == story_id:
            for t in s.get("tasks", []):
                if t["id"] == task_id:
                    t["done"] = not t.get("done", False)
                    break
            break
    _save(username, pid, {"stories": stories})
    return redirect(_safe_next(request.form.get("next"), url_for("backlog.backlog")))


@backlog_bp.route("/story/<story_id>/task/delete/<task_id>", methods=["POST"])
@project_required
def task_delete(story_id, task_id):
    username, pid = session["username"], session["project_id"]
    data    = get_project(username, pid)
    stories = data.get("stories", [])
    for s in stories:
        if s["id"] == story_id:
            s["tasks"] = [t for t in s.get("tasks", []) if t["id"] != task_id]
            break
    _save(username, pid, {"stories": stories})
    return redirect(_safe_next(request.form.get("next"), url_for("backlog.backlog")))

