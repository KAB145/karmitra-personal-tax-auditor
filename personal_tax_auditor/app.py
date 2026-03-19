"""
Personal Tax Auditor – Nepal
Flask Application Entry Point
"""

import os
import sys

# Allow imports from project root
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, session, redirect, url_for, send_from_directory
from models import init_db, close_db

# ── App factory ───────────────────────────────────────────────────────────────

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = os.environ.get("SECRET_KEY", "nepal-tax-auditor-dev-key-change-in-prod")
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit
    app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
    

    # Ensure upload dir exists
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Register blueprints (API routes)
    from routes.auth import auth_bp
    from routes.expenses import expenses_bp
    from routes.invoices import invoices_bp
    from routes.dashboard import dashboard_bp

    # Close DB connection after every request
    app.teardown_appcontext(close_db)

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(expenses_bp, url_prefix="/api")
    app.register_blueprint(invoices_bp, url_prefix="/api")
    app.register_blueprint(dashboard_bp, url_prefix="/api")

    # ── Page routes ────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        if "user_id" in session:
            return redirect(url_for("dashboard_page"))
        return render_template("landing.html")

    @app.route("/login")
    def login_page():
        if "user_id" in session:
            return redirect(url_for("dashboard_page"))
        return render_template("auth.html", mode="login")

    @app.route("/register")
    def register_page():
        if "user_id" in session:
            return redirect(url_for("dashboard_page"))
        return render_template("auth.html", mode="register")

    @app.route("/dashboard")
    def dashboard_page():
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return render_template("dashboard.html")

    @app.route("/expenses")
    def expenses_page():
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return render_template("expenses.html")

    @app.route("/invoices")
    def invoices_page():
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return render_template("invoices.html")

    @app.route("/report")
    def report_page():
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return render_template("report.html")

    @app.route("/profile")
    def profile_page():
        if "user_id" not in session:
            return redirect(url_for("login_page"))
        return render_template("profile.html")

    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    return app


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    app = create_app()
    print("✅  Nepal Personal Tax Auditor running on http://localhost:5000")
    app.run(debug=True, port=5000)


