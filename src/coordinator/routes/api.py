from flask import Blueprint, jsonify, request
from utils.jwt_helper import token_required
import random
import asyncio
import httpx

from utils import constants

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
    server_to_join = constants.CHAT_SERVERS_URL[0]
        
    return jsonify({
        "server": server_to_join
    }), 200 

# TO DO

# Open conversation and leave previous one

# Leave server connection (And become offline)

# Create a new chat (Create a new chat)

# Leave a chat (Leave an specific group chat - Can't be a personal chat)

# Delete a chat (Only the owner can delete the chat)

