from flask import Blueprint, request, jsonify, current_app
from id_generator_lib import PostgresIdGenerator, DatabaseConn

api_bp = Blueprint("api", __name__)


@api_bp.route("/generate_id", methods=["POST"])
async def generate_id():
    data = request.get_json()

    # handle if there is no group name in request
    if "group_name" not in data:
        return jsonify(
            {"error": "Bad Request", "mensaje": "No hay group name en el request"}
        ), 400

    group_name = data["group_name"]

    host = current_app.config.get("POSTGRES_HOST")
    database_conn = DatabaseConn(host)
    database_conn.try_init_database()

    postgres_id_generator = PostgresIdGenerator(database_conn)
    new_id = postgres_id_generator.generate_new_id(group_name)

    database_conn.close_connection()

    return jsonify({"generated_id": new_id}), 200
