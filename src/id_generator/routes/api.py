from flask import Blueprint, request, jsonify, current_app, g
from id_generator_lib import PostgresIdGenerator, DatabaseConn
import asyncio
import logging


api_bp = Blueprint("api", __name__)


def get_pg_db():
    # Si no hay una conexión abierta en esta petición, la creamos
    if 'pg_db' not in g:
        host = current_app.config.get('POSTGRES_HOST')
        database_conn = DatabaseConn(host)
        database_conn.try_init_database()
        g.pg_db = database_conn

    return g.pg_db


# Aquí ocurre la magia del cierre automático
@api_bp.teardown_request
def close_pg_db(exception=None):
    # Extraemos la conexión de 'g' si es que se llegó a abrir
    database_conn = g.pop('pg_db', None)
    
    if database_conn is not None:
        logging.info("Closing PG Database...")
        database_conn.close_connection()


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

    database_conn = get_pg_db()
    postgres_id_generator = PostgresIdGenerator(database_conn)
    new_id = postgres_id_generator.generate_new_id(group_name)

    return jsonify({
        "generated_id": new_id
    }), 200
