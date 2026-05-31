from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time


def _safe_next(next_url, fallback):
    """Only follow next= if it is a relative path (prevents open redirect)."""
    if next_url:
        p = urlparse(next_url)
        if not p.scheme and not p.netloc:
            return next_url
    return fallback

dashboard_bp = Blueprint("dashboard", __name__)


def _save(username, pid, fields):
    """Update a single project document identified by username + project_id."""
    projects.update_one(
        {"username": username, "project_id": pid},
        {"$set": fields}
    )


# ── PROJECT MANAGEMENT ────────────────────────────────────

@dashboard_bp.route("/projects")
@login_required
def projects_home():
    session.pop("project_id", None)
    username = session["username"]
    all_docs = list(projects.find({"username": username}))

    # Migrate any legacy document that has no project_id
    for doc in all_docs:
        if not doc.get("project_id"):
            pid = f"proj_{int(time.time())}"
            projects.update_one(
                {"_id": doc["_id"]},
                {"$set": {"project_id": pid}}
            )
            doc["project_id"] = pid   # patch in-memory so template sees it

    return render_template("dashboard/projects.html", projects=all_docs)


@dashboard_bp.route("/projects/create", methods=["POST"])
@login_required
def projects_create():
    username     = session["username"]
    project_name = request.form.get("project_name", "").strip() or "Untitled Project"
    pm           = request.form.get("pm", "").strip()
    project_id   = f"proj_{int(time.time())}"

    # Creates the document with defaults
    get_project(username, project_id)

    # Immediately set the display name and PM
    _save(username, project_id, {
        "project.name": project_name,
        "project.pm":   pm or username,
    })

    session["project_id"] = project_id
    return redirect(url_for("dashboard.overview"))


@dashboard_bp.route("/projects/switch/<project_id>", methods=["POST"])
@login_required
def projects_switch(project_id):
    username = session["username"]
    doc = projects.find_one({"username": username, "project_id": project_id})
    if not doc:
        # project_id not found — go back to the list so the user can try again
        return redirect(url_for("dashboard.projects_home"))
    session["project_id"] = project_id
    return redirect(url_for("dashboard.overview"))


@dashboard_bp.route("/projects/delete/<project_id>", methods=["POST"])
@login_required
def projects_delete(project_id):
    username = session["username"]
    doc = projects.find_one({"username": username, "project_id": project_id})
    if doc:
        projects.delete_one({"username": username, "project_id": project_id})
        if session.get("project_id") == project_id:
            session.pop("project_id", None)
    return redirect(url_for("dashboard.projects_home"))


@dashboard_bp.route("/projects/exit")
@login_required
def projects_exit():
    session.pop("project_id", None)
    return redirect(url_for("dashboard.projects_home"))


# ── OVERVIEW ──────────────────────────────────────────────

@dashboard_bp.route("/")
@project_required
def overview():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/overview.html", data=data)


@dashboard_bp.route("/overview/save", methods=["POST"])
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
    return redirect(url_for("dashboard.overview"))


# ── BACKLOG ───────────────────────────────────────────────

@dashboard_bp.route("/backlog")
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


@dashboard_bp.route("/backlog/add", methods=["POST"])
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
    return redirect(url_for("dashboard.backlog"))


@dashboard_bp.route("/backlog/edit/<story_id>", methods=["POST"])
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
    return redirect(url_for("dashboard.backlog"))


@dashboard_bp.route("/backlog/assign/<story_id>", methods=["POST"])
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
    return redirect(url_for("dashboard.backlog"))


@dashboard_bp.route("/backlog/delete/<story_id>", methods=["POST"])
@project_required
def backlog_delete(story_id):
    username, pid = session["username"], session["project_id"]
    data   = get_project(username, pid)
    stories = [s for s in data.get("stories", []) if s["id"] != story_id]
    _save(username, pid, {"stories": stories})
    return redirect(url_for("dashboard.backlog"))


# ── SPRINTS ───────────────────────────────────────────────

@dashboard_bp.route("/sprints/add", methods=["POST"])
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
    return redirect(url_for("dashboard.sprint_config"))



@dashboard_bp.route("/sprints/delete/<sprint_id>", methods=["POST"])
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
    return redirect(url_for("dashboard.sprint_config"))


# ── SPRINT BOARD ──────────────────────────────────────────

@dashboard_bp.route("/sprint")
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


@dashboard_bp.route("/sprint/story/move/<story_id>", methods=["POST"])
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
    return redirect(url_for("dashboard.sprint", sprint=request.form.get("sprint_id", "")))


@dashboard_bp.route("/sprint/story/back/<story_id>", methods=["POST"])
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
    return redirect(url_for("dashboard.sprint", sprint=request.form.get("sprint_id", "")))


# ── STORY TASKS ───────────────────────────────────────────

@dashboard_bp.route("/story/<story_id>/task/add", methods=["POST"])
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
    return redirect(_safe_next(request.form.get("next"), url_for("dashboard.backlog")))


@dashboard_bp.route("/story/<story_id>/task/toggle/<task_id>", methods=["POST"])
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
    return redirect(_safe_next(request.form.get("next"), url_for("dashboard.backlog")))


@dashboard_bp.route("/story/<story_id>/task/delete/<task_id>", methods=["POST"])
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
    return redirect(_safe_next(request.form.get("next"), url_for("dashboard.backlog")))


# ── RISKS ─────────────────────────────────────────────────

@dashboard_bp.route("/risks")
@project_required
def risks():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/risks.html", data=data)


@dashboard_bp.route("/risks/add", methods=["POST"])
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
    return redirect(url_for("dashboard.risks"))


@dashboard_bp.route("/risks/delete/<risk_id>", methods=["POST"])
@project_required
def risks_delete(risk_id):
    username, pid = session["username"], session["project_id"]
    data      = get_project(username, pid)
    risk_list = [r for r in data.get("risks", []) if r["id"] != risk_id]
    _save(username, pid, {"risks": risk_list})
    return redirect(url_for("dashboard.risks"))


# ── TEAM ──────────────────────────────────────────────────

@dashboard_bp.route("/team")
@project_required
def team():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/team.html", data=data)


@dashboard_bp.route("/team/add", methods=["POST"])
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
    return redirect(url_for("dashboard.team"))


@dashboard_bp.route("/team/delete/<member_id>", methods=["POST"])
@project_required
def team_delete(member_id):
    username, pid = session["username"], session["project_id"]
    data      = get_project(username, pid)
    team_list = [m for m in data.get("team", []) if m["id"] != member_id]
    _save(username, pid, {"team": team_list})
    return redirect(url_for("dashboard.team"))


# ── DEFINITION OF DONE ────────────────────────────────────

@dashboard_bp.route("/dod")
@project_required
def dod():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/dod.html", data=data)


@dashboard_bp.route("/dod/save", methods=["POST"])
@project_required
def dod_save():
    username, pid = session["username"], session["project_id"]
    data     = get_project(username, pid)
    dod_list = data.get("dod", [])
    checked  = request.form.getlist("checked")
    for item in dod_list:
        item["done"] = item["text"] in checked
    _save(username, pid, {"dod": dod_list})
    return redirect(url_for("dashboard.dod"))


# ── RETRO ─────────────────────────────────────────────────

@dashboard_bp.route("/retro")
@project_required
def retro():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/retro.html", data=data)


@dashboard_bp.route("/retro/add/<col>", methods=["POST"])
@project_required
def retro_add(col):
    if col not in ["went", "improve", "action"]:
        return redirect(url_for("dashboard.retro"))
    username, pid = session["username"], session["project_id"]
    data  = get_project(username, pid)
    item  = {"id": f"re_{int(time.time())}", "text": request.form.get("text", "").strip()}
    if item["text"]:
        retro = data.get("retro", {"went": [], "improve": [], "action": []})
        retro[col].append(item)
        _save(username, pid, {"retro": retro})
    return redirect(url_for("dashboard.retro"))


@dashboard_bp.route("/retro/delete/<col>/<item_id>", methods=["POST"])
@project_required
def retro_delete(col, item_id):
    if col not in ["went", "improve", "action"]:
        return redirect(url_for("dashboard.retro"))
    username, pid = session["username"], session["project_id"]
    data  = get_project(username, pid)
    retro = data.get("retro", {"went": [], "improve": [], "action": []})
    retro[col] = [i for i in retro[col] if i["id"] != item_id]
    _save(username, pid, {"retro": retro})
    return redirect(url_for("dashboard.retro"))


# ── COMMUNICATION PLAN ────────────────────────────────────

@dashboard_bp.route("/comms")
@project_required
def comms():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/comms.html", data=data)


@dashboard_bp.route("/comms/add", methods=["POST"])
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
    return redirect(url_for("dashboard.comms"))


@dashboard_bp.route("/comms/delete/<item_id>", methods=["POST"])
@project_required
def comms_delete(item_id):
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    lst  = [c for c in data.get("comms", []) if c["id"] != item_id]
    _save(username, pid, {"comms": lst})
    return redirect(url_for("dashboard.comms"))


# ── STAKEHOLDERS ──────────────────────────────────────────

@dashboard_bp.route("/stakeholders")
@project_required
def stakeholders():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/stakeholders.html", data=data)


@dashboard_bp.route("/stakeholders/add", methods=["POST"])
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
    return redirect(url_for("dashboard.stakeholders"))


@dashboard_bp.route("/stakeholders/delete/<item_id>", methods=["POST"])
@project_required
def stakeholders_delete(item_id):
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    lst  = [s for s in data.get("stakeholders", []) if s["id"] != item_id]
    _save(username, pid, {"stakeholders": lst})
    return redirect(url_for("dashboard.stakeholders"))


# ── ROLES & RESPONSIBILITY ────────────────────────────────

@dashboard_bp.route("/raci")
@project_required
def raci():
    data = get_project(session["username"], session["project_id"])
    return render_template("dashboard/raci.html", data=data)


@dashboard_bp.route("/raci/add", methods=["POST"])
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
    return redirect(url_for("dashboard.raci"))


@dashboard_bp.route("/raci/delete/<item_id>", methods=["POST"])
@project_required
def raci_delete(item_id):
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    lst  = [r for r in data.get("raci", []) if r["id"] != item_id]
    _save(username, pid, {"raci": lst})
    return redirect(url_for("dashboard.raci"))


# ── SPRINT CONFIGURATION ──────────────────────────────────

@dashboard_bp.route("/sprint-config")
@project_required
def sprint_config():
    data         = get_project(session["username"], session["project_id"])
    sprints_list = data.get("sprints", [])
    return render_template("dashboard/sprint_config.html", data=data, sprints=sprints_list)


@dashboard_bp.route("/sprint-config/save", methods=["POST"])
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
    return redirect(url_for("dashboard.sprint_config"))


@dashboard_bp.route("/sprint-config/dor/delete/<int:idx>", methods=["POST"])
@project_required
def dor_delete(idx):
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)
    dor  = data.get("dor", [])
    if 0 <= idx < len(dor):
        del dor[idx]
        _save(username, pid, {"dor": dor})
    return redirect(url_for("dashboard.sprint_config"))


# ── ANALYTICS ─────────────────────────────────────────────

@dashboard_bp.route("/analytics")
@project_required
def analytics():
    import json
    username, pid = session["username"], session["project_id"]
    data = get_project(username, pid)

    stories = data.get("stories", [])

    # Sprint board — count by story status field (replaces old kanban cards)
    sprint_stories = [s for s in stories if s.get("sprint_id")]
    sprint = {
        "todo":   sum(1 for s in sprint_stories if s.get("status", "todo") == "todo"),
        "inprog": sum(1 for s in sprint_stories if s.get("status") == "inprog"),
        "done":   sum(1 for s in sprint_stories if s.get("status") == "done"),
    }

    priority = {
        "high": sum(1 for s in stories if s.get("priority") == "high"),
        "med":  sum(1 for s in stories if s.get("priority") == "med"),
        "low":  sum(1 for s in stories if s.get("priority") == "low"),
    }

    buckets = {"1-3": 0, "4-6": 0, "7-9": 0, "10-13": 0, "14+": 0}
    for s in stories:
        p = int(s.get("pts") or 0)
        if   p <= 3:  buckets["1-3"]   += 1
        elif p <= 6:  buckets["4-6"]   += 1
        elif p <= 9:  buckets["7-9"]   += 1
        elif p <= 13: buckets["10-13"] += 1
        else:         buckets["14+"]   += 1

    phases       = data.get("phases", [])
    phase_done   = sum(1 for p in phases if p.get("state") == "done")
    phase_active = sum(1 for p in phases if p.get("state") == "active")
    phase_todo   = sum(1 for p in phases if p.get("state") == "todo")

    risks = data.get("risks", [])
    risk_counts = {
        "high": sum(1 for r in risks if r.get("level") == "high"),
        "med":  sum(1 for r in risks if r.get("level") == "med"),
        "low":  sum(1 for r in risks if r.get("level") == "low"),
    }

    dod      = data.get("dod", [])
    dod_done = sum(1 for d in dod if d.get("done"))

    all_tasks  = [t for s in stories for t in s.get("tasks", [])]
    tasks_done = sum(1 for t in all_tasks if t.get("done"))

    chart_data = json.dumps({
        "sprint":           sprint,
        "priority":         priority,
        "pts_buckets":      buckets,
        "phase_done":       phase_done,
        "phase_active":     phase_active,
        "phase_todo":       phase_todo,
        "risk_counts":      risk_counts,
        "dod_done":         dod_done,
        "dod_total":        len(dod),
        "total_stories":    len(stories),
        "sprint_assigned":  len(sprint_stories),
        "tasks_done":       tasks_done,
        "tasks_total":      len(all_tasks),
        "team_size":        len(data.get("team", [])),
    })

    return render_template("dashboard/analytics.html", data=data, chart_data=chart_data)
