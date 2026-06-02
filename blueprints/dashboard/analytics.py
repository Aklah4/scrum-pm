from flask import Blueprint, render_template, request, session, redirect, url_for
from blueprints.utils import login_required, project_required
from db import projects, get_project
from urllib.parse import urlparse
import time


analytics_bp = Blueprint("analytics", __name__, url_prefix="/dashboard/analytics")
# ── ANALYTICS ─────────────────────────────────────────────

@analytics_bp.route("/analytics")
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
