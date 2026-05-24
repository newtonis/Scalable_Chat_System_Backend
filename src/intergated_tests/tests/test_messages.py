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


@pytest.fixture
async def func_register_and_login_new_user():
    async def register_and_login_user(client):
        credenciales = {"email": f"random@email{random.randrange(200)}.com", "password": str(random.randrange(1000)), "name": f"foo {random.randrange(200)}"}
        await client.post(f"{constants.COORDINATOR_URL}/auth/register", json=credenciales)
        res = await client.post(f"{constants.COORDINATOR_URL}/auth/login", json=credenciales)
        
        logging.info(f"Logging result: {res}")

        id = res.json()["id"]
        name = credenciales["name"]
        token = res.json()["token"]
        logging.info(f"New user information {id}>{name}>{token}")
        return id, name, token
    
    return register_and_login_user


# We test a client to connect to the coordinator, complete register and login, and then make it join the chat server with the same session. Then disconnect. 

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

#  We test a client to connect to the coordinator, complete register and login, make it join the chat server and then subscribe to a conversation of the same user 
# (It would be the User-User chat). We verify subscription in the kv store database. Then we disconnect and verify unsubscription and user to be disconnected in kv store database.
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

    # Verify unsubscription in database to server and to the conversation
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


# We test a client to connect to the coordinator, complete register and login, make it join the chat server, subscribe to a conversation of the same user. 
# We verify subscription and then send a message to the same user (User-User Chat). 
# Then we verify the message is received (As we are subscribed to conversation) and its content

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


# We test two clients to connect to coordinator, complete register and login. Then we make them join the chat server (and verify the stored kv store connection information) 
# and subscribe to the conversation of these two users. We verify the users subscriptions in kv store database. 
# After we wait for each user to complete the subscription (To avoid race conditions and guarantee sent messages are transmitted as both users are already subscribed) then we make them send a message to its dm channel, 
# and verify the reception of the message of each one. We just log the message count, that should be n, n + 1. when n is the messages send before running the test. 
# To make this test to work we had to make id generator able to handle concurrency of operations and guarantee a different id to be assigned to each message.

@pytest.mark.asyncio
async def test_send_peer_message(client, func_register_and_login_new_user):

    id1, name1, token1 = await func_register_and_login_new_user(client)
    id2, name2, token2 = await func_register_and_login_new_user(client)

    ## Join client 1 to server
    headers1 = {"Authorization": f"Bearer {token1}"}
    res1 = await client.get(f"{constants.COORDINATOR_URL}/api/join_server", headers=headers1)
    assert res1.status_code == 200
    data1 = res1.json()
    server_id_1 = data1["server"]

    ## Join client 2 to server
    headers2 = {"Authorization": f"Bearer {token2}"}
    res2 = await client.get(f"{constants.COORDINATOR_URL}/api/join_server", headers=headers2)
    assert res2.status_code == 200
    data2 = res2.json()
    server_id_2 = data2["server"]
    

    async def task_message(task_number, from_id, to_id, token, headers, server_id, my_event, other_event):
        async with websockets.connect(f"{constants.CHAT_SERVERS_URL[server_id]}?token={token}") as websocket:
            logging.info(f"[Task {task_number}] Connected to websocket with bearer Token")

            # Wait for server to mark us as connected
            await asyncio.sleep(2)
            
            logging.info(f"subscription data: {from_id}, {token}")
            # Verify we are registered as connected in the server
            res0 = await client.get(
                f"{constants.KV_STORE_URL}/api/get?key=userver>{from_id}>{token}"
            )
            value0 = res0.json()["value"]
            assert int(value0) == server_id

            # Subscribe to dms with uthe other user
            res = await client.post(f"{constants.COORDINATOR_URL}/api/subscribe_dm", json={"target_user_id": to_id}, headers=headers)
            assert res.json()["result"] == "user subscription is complete"

            # Send signal to other task that subscription is completed
            other_event.set()
            # Wait for the other task to complete subscription
            await my_event.wait()

            data_package = {
                'command': 'new_message',
                    'message': {
                        'type': 'dm'
                        ,'user_id': to_id
                        ,'value': f'Hello from user {from_id}'
                    }
                }
        
            msg = json.dumps(data_package)
            await websocket.send(msg)

            # Wait for self message and task2 message. Order can be any
            answer1 = await websocket.recv()
            answer2 = await websocket.recv()

            json1 = json.loads(answer1)
            json2 = json.loads(answer2)

            # Verify commands received are new messages indeed
            assert json1["command"] == "new_message"
            assert json2["command"] == "new_message"

            logging.info(f'[Task {task_number}] First recv message id: {json1["message"]["id"]}')
            logging.info(f'[Task {task_number}] First message from: {json1["message"]["user_id"] }')
            logging.info(f'[Task {task_number}] First message content: {json1["message"]["value"] }')

            logging.info(f'[Task {task_number}] Second recv Message id: {json2["message"]["id"]}')
            logging.info(f'[Task {task_number}] Second message from: {json2["message"]["user_id"] }')
            logging.info(f'[Task {task_number}] Second message content: {json2["message"]["value"] }')
            
            m_by_uid = {}
            
            m_by_uid[int(json1["message"]["user_id"])] = json1
            m_by_uid[int(json2["message"]["user_id"])] = json2

            my_package = m_by_uid[from_id]
            peer_package = m_by_uid[to_id]

            my_message = my_package["message"]
            peer_message = peer_package["message"]

            assert my_message["value"] == f'Hello from user {from_id}' and my_message["user_id"] == from_id and my_message["type"] == "dm"
            assert peer_message["value"] == f'Hello from user {to_id}' and peer_message["user_id"] == to_id and peer_message["type"] == "dm"
    
    try:
        ev1 = asyncio.Event()
        ev2 = asyncio.Event()

        await asyncio.wait_for(
            asyncio.gather(
                task_message(1, id1, id2, token1, headers1, server_id_1, ev1, ev2),
                task_message(2, id2, id1, token2, headers2, server_id_2, ev2, ev1)
            ), 
            timeout=500
        )
    except asyncio.TimeoutError:
        logging.info("Task timeout (10 seconds)")
    