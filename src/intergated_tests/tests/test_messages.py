import pytest
from utils import constants
import asyncio
import httpx
import websockets
import json
import logging
import random
import contextvars


@pytest.fixture
async def client():
    return httpx.AsyncClient()


@pytest.fixture
async def usuario_registrado(client):
    # Register user with its password
    credenciales = {"email": "test@example.com", "password": "1234", "name": "test"}
    await client.post(f"{constants.COORDINATOR_URL}/auth/register", json=credenciales)
    return credenciales


@pytest.fixture
async def login_result(client, usuario_registrado):
    # Get validated token
    res = await client.post(f"{constants.COORDINATOR_URL}/auth/login", json=usuario_registrado)
    return res


@pytest.fixture
async def valid_token(login_result):
    return login_result.json()["token"]


@pytest.fixture
def user_id(login_result):
    return login_result.json()["id"]


@pytest.mark.asyncio
async def test_subscribe_to_conversation(client, valid_token, user_id):

    # Conect client to serverpp
    headers = {"Authorization": f"Bearer {valid_token}"}

    res = await client.get(f"{constants.COORDINATOR_URL}/api/join_server", headers=headers)

    assert res.status_code == 200
    data = res.json()
    server_id = data["server"]

    # Open websocket connection to mark user as connected to server
    
    async with websockets.connect(f"{constants.CHAT_SERVERS_URL[server_id]}?token={valid_token}") as websocket:
        logging.info("Connected to websocker with bearer Token")

        # Wait for server to mark us as connected
        await asyncio.sleep(2)

        # Call subscribe endpoint

        res = await client.post(f"{constants.COORDINATOR_URL}/api/subscribe_dm", json={"target_user_id": user_id}, headers=headers)

        assert res.json()["result"] == "user subscription is complete"

        logging.info("User subscription is completed")
        # Verify data from KV Store
        
        message_group = "dm" + "<" + str(user_id) + "<" + str(user_id)

        response = await client.get(
            f"{constants.KV_STORE_URL}/api/get?key={message_group}>{server_id}>{user_id}>{valid_token}"
        )
        logging.info(f"subpscription value: {response.json()}")
        value = response.json()["value"]
        # Assert subscription is registered
        assert value == 'true'

        logging.info("Subscription is verified")
