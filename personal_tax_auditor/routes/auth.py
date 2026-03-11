from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from models import create_user, get_user_by_email, get_user_by_id, update_user_profile, get_db

auth_bp = Blueprint("auth", __name__)


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    name     = (data.get("name") or "").strip()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    pan      = (data.get("pan_number") or "").strip()
    salary   = float(data.get("salary") or 0)
    employer = (data.get("employer") or "").strip()

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    ok = create_user(name, email, generate_password_hash(password), pan, salary, employer)
    if not ok:
        return jsonify({"error": "Email already registered"}), 409

    user = get_user_by_email(email)
    session["user_id"] = user["id"]
    return jsonify({"message": "Registration successful", "user": {"id": user["id"], "name": name}}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data     = request.get_json()
    email    = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    return jsonify({"message": "Login successful", "user": {"id": user["id"], "name": user["name"]}}), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"}), 200


@auth_bp.route("/profile", methods=["GET"])
@login_required
def get_profile():
    user = get_user_by_id(session["user_id"])
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "id":         user["id"],
        "name":       user["name"],
        "email":      user["email"],
        "pan_number": user["pan_number"],
        "salary":     user["salary"],
        "employer":   user["employer"],
    }), 200


@auth_bp.route("/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json()
    update_user_profile(
        session["user_id"],
        (data.get("name") or "").strip(),
        (data.get("pan_number") or "").strip(),
        float(data.get("salary") or 0),
        (data.get("employer") or "").strip(),
    )
    return jsonify({"message": "Profile updated"}), 200


@auth_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    data     = request.get_json()
    current  = data.get("current_password") or ""
    new_pass = data.get("new_password") or ""
    confirm  = data.get("confirm_password") or ""

    if not current or not new_pass or not confirm:
        return jsonify({"error": "All three fields are required"}), 400
    if len(new_pass) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400
    if new_pass != confirm:
        return jsonify({"error": "New passwords do not match"}), 400

    user = get_user_by_id(session["user_id"])
    if not check_password_hash(user["password_hash"], current):
        return jsonify({"error": "Current password is incorrect"}), 401

    conn = get_db()
    conn.execute("UPDATE users SET password_hash=? WHERE id=?",
                 (generate_password_hash(new_pass), session["user_id"]))
    conn.commit()
    return jsonify({"message": "Password changed successfully"}), 200


@auth_bp.route("/delete-account", methods=["DELETE", "POST"])
@login_required
def delete_account():
    conn = get_db()
    uid  = session["user_id"]
    conn.execute("DELETE FROM expenses    WHERE user_id=?", (uid,))
    conn.execute("DELETE FROM invoices    WHERE user_id=?", (uid,))
    conn.execute("DELETE FROM tax_reports WHERE user_id=?", (uid,))
    conn.execute("DELETE FROM users       WHERE id=?",      (uid,))
    conn.commit()
    session.clear()
    return jsonify({"message": "Account deleted"}), 200


@auth_bp.route("/session", methods=["GET"])
def check_session():
    if "user_id" in session:
        user = get_user_by_id(session["user_id"])
        return jsonify({"logged_in": True, "user": {"id": user["id"], "name": user["name"]}}), 200
    return jsonify({"logged_in": False}), 200
