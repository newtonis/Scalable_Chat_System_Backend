from flask import Blueprint, jsonify, request, current_app
from utils.jwt_helper import token_required
import random
import asyncio
import httpx
from utils import constants, users
from utils.users import user_registrator
import logging


protected_bp = Blueprint("protected", __name__)

# Join to the more convenient socket server
@protected_bp.route("/join_server", methods=["GET"])
@token_required
async def join_server():
    # Random criteria, 
    # Better option: replace with regional criteria
    
    #server_to_join = constants.CHAT_SERVERS_URL[random.randrange(len(constants.CHAT_SERVERS_URL))]
    server_to_join = 0 # Join to server of id 0
        
    return jsonify({
        "server": server_to_join
    }), 200 

# Get total users (To be able to know who to send messages)
@protected_bp.route("/get_total_users", methods=["GET"])
@token_required
async def get_total_users():
    return jsonify({"users":
        user_registrator.get_all_users()
    }) , 200 


# Subscribe to a dm conversation
@protected_bp.route("/subscribe_dm", methods=["POST"])
@token_required
async def subscribe_dm():
    KV_STORE_URL = current_app.config.get('KV_STORE_URL')

    data = request.get_json()
    if not "target_user_id" in data:
        logging.info("No target user id in data")

        return jsonify({"result":
            "No target user in package"
        }) , 400 
    logging.info(request.user_id)
    # TODO: Validate that the target user id is valid (exists in the system)
    
    target_user_id = int(data["target_user_id"])

    user_id = int(request.user_id)
    session_token = request.token

    # Get which server user is connected, so we subscribe the user to the group in the corresponding server
    # For now the server is always 0

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{KV_STORE_URL}/api/get?key=userver>{user_id}>{session_token}",
        )
    data = response.json()
    logging.info(f"Response from kv store for server number: {data}")

    server_id = data["value"]
    message_group = "dm" + "<" + str(min(user_id, target_user_id)) + "<" + str(max(user_id, target_user_id))
    session_token = request.token

    subscription_info = {
        "key": f"usubscription>{message_group}>{server_id}>{user_id}>{session_token}"
        ,"value": 'true'
    }
    logging.info(f"DM Subscription to complete: {subscription_info}")

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{KV_STORE_URL}/api/set", 
            json=subscription_info
        )
    logging.info("Subscription completed")


    return jsonify({"result":
        "user subscription is complete"
    }) , 200  


# Subscribe to a group conversation
@protected_bp.route("/subscribe_group", methods=["POST"])
@token_required
async def subscribe_group():
    return jsonify({"error": "Not implemented"}), 501

# Get specific dm messages
@protected_bp.route("/get_dm_messages", methods=["GET"])
@token_required
async def get_dm_messages():
    return jsonify({"error": "Not implemented"}), 501

# Get specific group messages
@protected_bp.route("/get_group_messages", methods=["GET"])
@token_required
async def get_group_messages():
    return jsonify({"error": "Not implemented"}), 501

# Delete a chat (Only the owner can delete the chat)
@protected_bp.route("/delete_chat", methods=["POST"])
@token_required
async def delete_chat():
    return jsonify({"error": "Not implemented"}), 501

