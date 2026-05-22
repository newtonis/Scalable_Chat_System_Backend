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
async def test_connect_and_disconnect(client, valid_token, user_id):
    headers = {"Authorization": f"Bearer {valid_token}"}

    res = await client.get(f"{constants.COORDINATOR_URL}/api/join_server", headers=headers)

    assert res.status_code == 200
    data = res.json()
    server_id = data["server"]

    # Open websocket connection to mark user as connected to server
    
    async with websockets.connect(f"{constants.CHAT_SERVERS_URL[server_id]}?token={valid_token}") as websocket:
        logging.info("Connected to websocker with bearer Token")

        await asyncio.sleep(20)

        logging.info("Wait time ended, disconnecting")


@pytest.mark.asyncio
async def test_subscribe_to_conversation(client, valid_token, user_id):

    # Conect client to serverpp
    headers = {"Authorization": f"Bearer {valid_token}"}

    res = await client.get(f"{constants.COORDINATOR_URL}/api/join_server", headers=headers)

    assert res.status_code == 200
    data = res.json()
    server_id = data["server"]

    # Open websocket connection to mark user as connected to serve
    async with websockets.connect(f"{constants.CHAT_SERVERS_URL[server_id]}?token={valid_token}") as websocket:
        logging.info("Connected to websocker with bearer Token")

        # Wait for server to mark us as connected
        await asyncio.sleep(2)

        # Verify we are registered as connected in the server
        res0 = await client.get(
            f"{constants.KV_STORE_URL}/api/get?key=userver>{user_id}>{valid_token}"
        )
        value0 = res0.json()["value"]
        assert int(value0) == server_id

        # Call subscribe endpoint
        res = await client.post(f"{constants.COORDINATOR_URL}/api/subscribe_dm", json={"target_user_id": user_id}, headers=headers)
        assert res.json()["result"] == "user subscription is complete"

        logging.info("User subscription is completed")
        # Verify data from KV Store
        
        message_group = "dm" + "<" + str(user_id) + "<" + str(user_id)

        response = await client.get(
            f"{constants.KV_STORE_URL}/api/get?key=usubscription>{message_group}>{server_id}>{user_id}>{valid_token}"
        )
        logging.info(f"subpscription value: {response.json()}")
        value = response.json()["value"]
        # Assert subscription is registered
        assert value == 'true'

        logging.info("Subscription is verified")
    
    # Wait for server to cancel subscription
    await asyncio.sleep(2)

    # Verify unsubpscrition in database to server and to the conversation
    response = await client.get(
        f"{constants.KV_STORE_URL}/api/get?key=usubscription>{message_group}>{server_id}>{user_id}>{valid_token}"
    )
    value = response.json()["value"]
    assert value is None

    response2 = await client.get(
        f"{constants.KV_STORE_URL}/api/get?key=userver>{user_id}>{valid_token}"
    )
    value2 = response2.json()["value"]

    assert value2 is None


# Send a Direct Message to Myself
@pytest.mark.asyncio
async def test_send_direct_message(client, valid_token, user_id):
    # Conect client to server
    headers = {"Authorization": f"Bearer {valid_token}"}

    res = await client.get(f"{constants.COORDINATOR_URL}/api/join_server", headers=headers)
    assert res.status_code == 200
    data = res.json()
    server_id = data["server"]

    # Try to establish websocket server connection
    logging.info(f"Connecting to {constants.CHAT_SERVERS_URL[server_id]} ...")
    
    async with websockets.connect(f"{constants.CHAT_SERVERS_URL[server_id]}?token={valid_token}") as websocket:
        logging.info("Connected to websocket with bearer Token")
    
        # Wait for server to mark us as connected
        await asyncio.sleep(2)

        # Complete subscription
        res = await client.post(f"{constants.COORDINATOR_URL}/api/subscribe_dm", json={"target_user_id": user_id}, headers=headers)

        assert res.json()["result"] == "user subscription is complete"

        data_package = {
            'command': 'new_message',
            'message': {
                'type': 'dm'
                ,'user_id': user_id
                ,'value': 'test message'
            }
        }
        msg = json.dumps(data_package)
        await websocket.send(msg)

        # Wait for the message to be sent back
        respuesta = await websocket.recv()
        logging.info(f"Servidor dice: {respuesta}")

        rta_json = json.loads(respuesta)

        assert rta_json["command"] == 'new_message'

        logging.info(f'Message id: {rta_json["message"]["id"]}')

        assert rta_json["message"]["value"] == 'test message' and int(rta_json["message"]["user_id"]) == user_id and rta_json["message"]["type"] == "dm"



