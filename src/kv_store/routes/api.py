from flask import Blueprint, current_app, jsonify, request
from kv_store_lib import RedisKVStore

api_bp = Blueprint("api", __name__)


@api_bp.route("/set", methods=["POST"])
async def set():
    data = request.get_json()

    if "value" not in data or "value" == None:
        return jsonify({"error": "data to write is None"}), 400

    key = data["key"]
    content = data["value"]

    host = current_app.config.get("REDIS_HOST")
    my_kv_store = RedisKVStore(host)
    await my_kv_store.set(key, content)
    await my_kv_store.close()

    return jsonify({"status": "Data written"}), 200


@api_bp.route("/get", methods=["GET"])
async def get():
    key = request.args.get("key")

    host = current_app.config.get("REDIS_HOST")
    my_kv_store = RedisKVStore(host)
    value = await my_kv_store.get(key)
    await my_kv_store.close()

    return {"value": value}


@api_bp.route("/delete", methods=["POST"])
async def delete():
    data = request.get_json()

    key = data["key"]

    host = current_app.config.get("REDIS_HOST")
    my_kv_store = RedisKVStore(host)
    await my_kv_store.delete(key)
    await my_kv_store.close()

    return {"status": "Data deleted"}


@api_bp.route("/get_all_with_prefix", methods=["GET"])
async def get_all_with_prefix():
    prefix = request.args.get("prefix")

    host = current_app.config.get("REDIS_HOST")
    my_kv_store = RedisKVStore(host)

    answer = {}
    async for key, value in my_kv_store.get_all_with_prefix(prefix):
        answer[key] = value

    await my_kv_store.close()

    return {"value": answer}


@api_bp.route("/delete_all_with_suffix", methods=["POST"])
async def delete_all_with_suffix():
    data = request.get_json()

    if "suffix" not in data:
        return jsonify({"error": "No suffix in data"}), 400

    # Delete all keys with A sepcific suffix
    suffix = data["suffix"]

    host = current_app.config.get("REDIS_HOST")
    my_kv_store = RedisKVStore(host)

    await my_kv_store.delete_all_with_suffix(suffix)
    await my_kv_store.close()

    return jsonify({"status": "Data deleted"}), 200


@api_bp.route("/delete_all_with_prefix_and_suffix", methods=["POST"])
async def delete_all_with_prefix_and_suffix():
    data = request.get_json()

    if "prefix" not in data:
        return jsonify({"error": "No prefix in data"}), 400

    if "suffix" not in data:
        return jsonify({"error": "No suffix in data"}), 400

    # Delete all keys with A sepcific suffix and prefix
    prefix = data["prefix"]
    suffix = data["suffix"]

    host = current_app.config.get("REDIS_HOST")
    my_kv_store = RedisKVStore(host)

    await my_kv_store.delete_all_with_prefix_and_suffix(prefix, suffix)
    await my_kv_store.close()

    return jsonify({"status": "Data deleted"}), 200
