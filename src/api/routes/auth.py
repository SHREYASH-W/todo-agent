"""
Authentication API endpoints.

POST /api/auth/register        - Create account
POST /api/auth/login           - Login
POST /api/auth/logout          - Logout
POST /api/auth/reset-password  - Reset password

Requirements: Authentication requirements
"""

from flask import Blueprint, jsonify, request, g

from src.engine.auth_service import AuthService, AuthError
from src.models import SessionLocal, Player

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
_auth = AuthService()


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username or not email or not password:
        return jsonify({"error": "username, email, and password are required"}), 400

    db = SessionLocal()
    try:
        # Check uniqueness
        if db.query(Player).filter(Player.username == username).first():
            return jsonify({"error": "Username already taken"}), 409
        if db.query(Player).filter(Player.email == email.lower()).first():
            return jsonify({"error": "Email already registered"}), 409

        try:
            player_data = _auth.register(username, email, password)
        except AuthError as e:
            return jsonify({"error": str(e)}), 400

        player = Player(**player_data)
        db.add(player)
        db.commit()
        db.refresh(player)

        return jsonify({
            "success": True,
            "player_id": player.id,
            "username": player.username,
        }), 201
    finally:
        db.close()


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username and password are required"}), 400

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.username == username).first()
        player_dict = None
        if player:
            player_dict = {
                "id": player.id,
                "username": player.username,
                "password_hash": player.password_hash,
            }

        try:
            token = _auth.login(username, password, player_dict)
        except AuthError as e:
            return jsonify({"error": str(e)}), 403

        if not token:
            return jsonify({"error": "Invalid credentials"}), 401

        # Update last login
        if player:
            from datetime import datetime
            player.last_login = datetime.utcnow()
            db.commit()

        return jsonify({
            "success": True,
            "session_token": token,
            "player_id": player.id if player else None,
        })
    finally:
        db.close()


@auth_bp.route("/logout", methods=["POST"])
def logout():
    data = request.get_json(silent=True) or {}
    token = data.get("session_token") or request.headers.get("Authorization", "").replace("Bearer ", "")

    if not token:
        return jsonify({"error": "session_token required"}), 400

    _auth.logout(token)
    return jsonify({"success": True})


@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    new_password = data.get("new_password", "")

    if not email or not new_password:
        return jsonify({"error": "email and new_password are required"}), 400

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.email == email).first()
        player_dict = {"id": player.id} if player else None

        try:
            success = _auth.reset_password(email, new_password, player_dict)
        except AuthError as e:
            return jsonify({"error": str(e)}), 400

        if success and player:
            player.password_hash = player_dict.get("password_hash", player.password_hash)
            db.commit()

        # Always return success to prevent email enumeration
        return jsonify({"success": True, "message": "If account exists, password has been reset."})
    finally:
        db.close()
