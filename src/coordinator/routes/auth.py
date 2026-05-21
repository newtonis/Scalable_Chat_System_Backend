from flask import Blueprint, request, jsonify
from utils.jwt_helper import generate_token

auth_bp = Blueprint("auth", __name__)

# Base de datos en memoria
users_db = {}


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email y contraseña son requeridos"}), 400

    email = data["email"]

    if email in users_db:
        return jsonify({"error": "El usuario ya existe"}), 409

    ## TODO: Change for a logic that support concurrency on user registration

    user_id = len(users_db) + 1
    users_db[email] = {
        "id": user_id,
        "email": email,
        "password": data["password"],  # TODO: Use hashing for password store
    }

    return jsonify({"mensaje": "Usuario registrado correctamente", "id": user_id}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data or not data.get("email") or not data.get("password"):
        return jsonify({"error": "Email y contraseña son requeridos"}), 400

    email = data["email"]
    user = users_db.get(email)

    if not user or user["password"] != data["password"]:
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = generate_token(str(user["id"]))
    return jsonify({"token": token}), 200
