from flask import Flask, session, redirect, url_for, render_template
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is not set")

# Harden session cookies.
# SESSION_COOKIE_SECURE is only enabled when running on Railway (HTTPS).
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"]   = os.getenv("RAILWAY_ENVIRONMENT") is not None

from blueprints.auth import auth_bp
from blueprints.dashboard import dashboard_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)


@app.context_processor
def inject_active_project():
    if "username" in session and "project_id" in session:
        from db import projects as proj_col
        doc = proj_col.find_one(
            {"username": session["username"], "project_id": session["project_id"]},
            {"project.name": 1}
        )
        if doc:
            return {"active_project_name": doc.get("project", {}).get("name", "")}
    return {"active_project_name": None}


@app.route("/")
def landing():
    if "username" in session:
        return redirect(url_for("dashboard.projects_home"))
    return render_template("landing.html")


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
