from flask import Blueprint, request, jsonify
from utils.jwt_helper import generate_token
from utils.users import user_registrator

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password") or not data.get("name"):
        return jsonify({"error": "Email, contraseña y Name son requeridos"}), 400

    email = data["email"]
    name = data["name"]
    password = data["password"]

    result, info = user_registrator.register_user(name, email, password)

    if not result and info['error'] == 'USER_REGISTERED':
        return jsonify({"error": "El usuario ya existe"}), 500
    elif result:
        return jsonify({"mensaje": "User registered", "id": info['results'] }), 201

    return jsonify({"mensaje": "Unexpected result"}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email y contraseña son requeridos"}), 400

    email = data["email"]
    password = data["password"]

    result, info = user_registrator.login_user(email, password)

    if not result and info["error"] == 'INVALID_EMAIL':
        return jsonify({"error": "Credenciales inválidas"}), 401
    elif not result and info["error"] == 'INVALID_PASSWORD':
        return jsonify({"error": "Credenciales inválidas"}), 401
    elif result:
        return jsonify({"name": info["name"], "id": info["id"], "token": info["token"]}), 200

    return jsonify({"mensaje": "Unexpected result"}), 500