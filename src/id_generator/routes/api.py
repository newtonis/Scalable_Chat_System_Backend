from flask import Blueprint, request, jsonify
from id_generator_lib import PostgresIdGenerator
import asyncio

api_bp = Blueprint("api", __name__)

@api_bp.route("/generate_id", methods=["POST"])
async def generate_id():
    data = request.get_json()
    
    # handle if there is no group name in request
    if not "group_name" in data:
        return jsonify({
            "error": "Bad Request",
            "mensaje": "No hay group name en el request"
        }), 400
    
    group_name = data["group_name"]

    postgres_id_generator = PostgresIdGenerator()
    new_id = postgres_id_generator.generate_new_id(group_name)

    return jsonify({
        "generated_id": new_id
    }), 200


