from flask import Flask, session, redirect, url_for, render_template
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise ValueError("SECRET_KEY environment variable is not set")


app.config["MAIL_SERVER"]         = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"]           = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"]        = os.getenv("MAIL_USE_TLS", "True") == "True"
app.config["MAIL_USE_SSL"]        = os.getenv("MAIL_USE_SSL", "False") == "True"
app.config["MAIL_USERNAME"]       = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"]       = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

# Harden session cookies.
# SESSION_COOKIE_SECURE is only enabled when running on Railway (HTTPS).
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"]   = os.getenv("RAILWAY_ENVIRONMENT") is not None

from blueprints.auth      import auth_bp
from blueprints.dashboard.projects import dashboard_bp
from blueprints.contactus import contactus_bp
from blueprints.about     import about_bp
from blueprints.careers   import careers_bp
from blueprints.legal     import legal_bp
from blueprints.privacy   import privacy_bp
from blueprints.security  import security_bp
from blueprints.support   import support_bp
from blueprints.dashboard.overview import overview_bp
from blueprints.dashboard.stakeholder import stakeholder_bp
from blueprints.dashboard.communication import comms_bp
from blueprints.dashboard.sprint import sprint_bp
from blueprints.dashboard.team import team_bp
from blueprints.dashboard.backlog import backlog_bp
from blueprints.dashboard.analytics import analytics_bp
from blueprints.dashboard.dod import dod_bp
from blueprints.dashboard.risks import risks_bp
from blueprints.dashboard.retro import retro_bp
from blueprints.dashboard.raci import raci_bp
from extensions import limiter, mail

limiter.init_app(app)
mail.init_app(app)





app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(contactus_bp)
app.register_blueprint(about_bp)
app.register_blueprint(careers_bp)
app.register_blueprint(legal_bp)
app.register_blueprint(privacy_bp)
app.register_blueprint(security_bp)
app.register_blueprint(support_bp)
app.register_blueprint(overview_bp)
app.register_blueprint(team_bp)
app.register_blueprint(stakeholder_bp)
app.register_blueprint(sprint_bp)
app.register_blueprint(backlog_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(comms_bp)
app.register_blueprint(dod_bp)
app.register_blueprint(risks_bp)
app.register_blueprint(retro_bp)
app.register_blueprint(raci_bp)



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
