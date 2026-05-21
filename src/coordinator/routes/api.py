from flask import Blueprint, jsonify, request
from utils.jwt_helper import token_required
import random
import asyncio
import httpx
from utils import constants, users

protected_bp = Blueprint("protected", __name__)

# Test of  protected endpoint
@protected_bp.route("/perfil", methods=["GET"])
@token_required
async def perfil():
    return jsonify({
        "mensaje": "Ruta protegida",
        "user_id": request.user_id
    }), 200

# Get the client server (if it is connected, and the open conversation)
@protected_bp.route("/get_user_state", methods=["GET"])
@token_required
async def get_user_state():
    return jsonify({
        "mensaje": "Ruta protegida",
        "user_id": request.user_id
    }), 200 

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

# Get total users
@protected_bp.route("/get_total_users", methods=["GET"])
@token_required
async def get_total_users():
    return 

# Subscribe to a dm conversation
@protected_bp.route("/subscribe_dm", methods=["POST"])
@token_required
async def subscribe_dm():
    pass

# Subscribe to a group conversation
@protected_bp.route("/subscribe_group", methods=["POST"])
@token_required
async def subscribe_group():
    pass

# Get specific dm messages
@protected_bp.route("/get_dm_messages", methods=["GET"])
@token_required
async def get_dm_messages():
    pass

# Get specific group messages
@protected_bp.route("/get_group_messages", methods=["GET"])
@token_required
async def get_group_messages():
    pass

# Leave server connection (And become offline)
@protected_bp.route("/exit_server", methods=["GET"])
@token_required
async def exit_server():
    pass

# Delete a chat (Only the owner can delete the chat)
@protected_bp.route("/delete_chat", methods=["POST"])
@token_required
async def delete_chat():
    pass

