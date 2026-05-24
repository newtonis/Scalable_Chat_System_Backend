import asyncio
import json
import logging
import random

import jwt
import pytest
import websockets
from utils import constants
from utils.users import user_registrator

from coordinator import app


# Test client with clean database on each test
@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "1234"
    app.config["KV_STORE_URL"] = constants.KV_STORE_URL.format(host="localhost")

    user_registrator.clean_db()

    with app.test_client() as client:
        yield client


# Register user with its password
@pytest.fixture
def usuario_registrado(client):
    credenciales = {"email": "test@example.com", "password": "1234", "name": "test"}
    client.post("/auth/register", json=credenciales)
    return credenciales


# Get validated token
@pytest.fixture
def token_valido(client, usuario_registrado):
    res = client.post("/auth/login", json=usuario_registrado)

    return res.get_json()["token"]


# Get user id of validated token
@pytest.fixture
def user_id(token_valido):
    payload = jwt.decode(token_valido, app.config["JWT_SECRET_KEY"], algorithms=["HS256"])
    return payload["sub"]


# Function to generate a new login user
@pytest.fixture
def func_register_and_login_new_user():
    def register_and_login_user(client_ref):
        credenciales = {
            "email": f"random@email{random.randrange(200)}.com",
            "password": str(random.randrange(1000)),
            "name": f"foo {random.randrange(200)}",
        }
        client.post("/auth/register", json=credenciales)
        res = client.post("/auth/login", json=credenciales)

        id = res.get_json()["id"]
        name = credenciales["name"]
        token = res.get_json()["token"]
        logging.info(f"New user information {id}>{name}>{token}")
        return id, name, token

    return register_and_login_user


# Verifies that the registration endpoint creates a new user and returns status 201.
def test_register(client):
    res = client.post(
        "/auth/register",
        json={"email": "nuevo@example.com", "password": "abcd", "name": "test"},
    )
    assert res.status_code == 201
    data = res.get_json()
    assert data["mensaje"] == "User registered"
    assert "id" in data


# Validates that login works with registered credentials and returns a JWT token.
def test_login(client, usuario_registrado):
    res = client.post("/auth/login", json=usuario_registrado)
    assert res.status_code == 200
    assert "token" in res.get_json()


# Checks protected access to the profile route using a valid JWT token.
def test_query_perfil(client, token_valido):
    res = client.get("/api/perfil", headers={"Authorization": f"Bearer {token_valido}"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["mensaje"] == "Ruta protegida"


# Registers three distinct users and verifies that the total user list includes them.
def test_register_three_users_and_check_existance(client, func_register_and_login_new_user):
    id1, name1, token1 = func_register_and_login_new_user(client)
    id2, name2, token2 = func_register_and_login_new_user(client)
    id3, name3, token3 = func_register_and_login_new_user(client)

    logging.info("Users created")

    res = client.get("/api/get_total_users", headers={"Authorization": f"Bearer {token1}"})

    data = res.get_json()

    logging.info(data)
    users = data["users"]

    assert len(users) == 3
    assert users[str(id1)] == name1
    assert users[str(id2)] == name2
    assert users[str(id3)] == name3


# Requests a chat server and verifies that the returned value is a valid index.
def test_join_server(client, token_valido, user_id):
    res = client.get("/api/join_server", headers={"Authorization": f"Bearer {token_valido}"})
    assert res.status_code == 200
    data = res.get_json()
    logging.info("Status code is 200")

    assert data["server"] >= 0 and data["server"] < len(constants.CHAT_SERVERS_URL)


# Validates that a chat server can be obtained and that a WebSocket connection can be made with the JWT token.
def test_server_connection(client, token_valido, user_id):
    headers = {"Authorization": f"Bearer {token_valido}"}

    res = client.get("/api/join_server", headers=headers)
    assert res.status_code == 200
    data = res.get_json()
    url = data["server"]

    # Try to establish websocket server connection
    logging.info(f"Connecting to {url} ...")

    async def query_user_server():
        async with websockets.connect(f"{url}?token={token_valido}") as websocket:
            logging.info("¡Conectado exitosamente al WebSocket con Token Bearer!")

            # Enviar un mensaje de prueba
            data_package = {"command": "dummy"}
            msg = json.dumps(data_package)
            await websocket.send(msg)
            respuesta = await websocket.recv()
            logging.info(f"Servidor dice: {respuesta}")

            return respuesta

    asyncio.run(query_user_server())
