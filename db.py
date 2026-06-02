from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

users    = db["users"]
projects = db["projects"]
contactus = db["contactus"]

# Compound unique index — one document per (user, project)
projects.create_index([("username", 1), ("project_id", 1)], unique=True)

# Unique indexes on users
users.create_index("username", unique=True)
users.create_index("email",    unique=True, sparse=True)


DEFAULT_PROJECT = {
    "project": {
        "name": "My Project",
        "client": "",
        "pm": "",
        "start": "",
        "end": "",
        "sprint_len": "2",
        "goal": ""
    },
    "phases": [
        {"label": "Discovery",       "state": "done"},
        {"label": "Sprint Planning", "state": "active"},
        {"label": "Sprint 1",        "state": "todo"},
        {"label": "Sprint 2",        "state": "todo"},
        {"label": "Sprint 3",        "state": "todo"},
        {"label": "UAT",             "state": "todo"},
        {"label": "Release",         "state": "todo"},
        {"label": "Retro",           "state": "todo"}
    ],
    "stories": [],
    "kanban":  {"todo": [], "inprog": [], "done": []},
    "risks":   [],
    "team":    [],
    "dod": [
        {"text": "Code reviewed by a peer",            "done": False},
        {"text": "Unit tests passing (>80% coverage)", "done": False},
        {"text": "No known high/critical bugs",        "done": False},
        {"text": "Acceptance criteria met",            "done": False},
        {"text": "Product Owner sign-off",             "done": False}
    ],
    "retro":  {"went": [], "improve": [], "action": []},
    "comms":  [],
    "stakeholders": [],
    "raci":   [],
    "sprint_cfg": {},
    "dor":    [],
    "sprints": [],
}


def get_project(username, project_id):
    doc = projects.find_one({"username": username, "project_id": project_id})
    if doc:
        return doc
    new_doc = {
        "username":    username,
        "project_id":  project_id,
        "created_at":  datetime.utcnow(),
    }
    new_doc.update(DEFAULT_PROJECT)
    projects.insert_one(new_doc)
    return projects.find_one({"username": username, "project_id": project_id})
