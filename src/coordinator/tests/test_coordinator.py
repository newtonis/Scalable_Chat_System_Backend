import pytest
from coordinator import app
from utils import constants
from routes import auth as auth_module
import asyncio
import httpx
import jwt
import websockets
import json
import logging


@pytest.fixture
def client():
    """Cliente de prueba con base de datos limpia en cada test."""
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "1234"
    auth_module.users_db.clear()

    with app.test_client() as client:
        yield client


@pytest.fixture
def usuario_registrado(client):
    """Registra un usuario base y retorna sus credenciales."""
    credenciales = {"email": "test@example.com", "password": "1234"}
    client.post("/auth/register", json=credenciales)
    return credenciales


@pytest.fixture
def token_valido(client, usuario_registrado):
    """Retorna un token JWT válido para el usuario registrado."""
    res = client.post("/auth/login", json=usuario_registrado)
    
    return res.get_json()["token"]


@pytest.fixture
def user_id(client, token_valido):
    payload = jwt.decode(
        token_valido,
        app.config["JWT_SECRET_KEY"],
        algorithms=["HS256"]
    )
    return payload["sub"]


def test_register(client):
    res = client.post("/auth/register", json={
        "email": "nuevo@example.com",
        "password": "abcd"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["mensaje"] == "Usuario registrado correctamente"
    assert "id" in data


def test_login(client, usuario_registrado):
    res = client.post("/auth/login", json=usuario_registrado)
    assert res.status_code == 200
    assert "token" in res.get_json()


def test_query_perfil(client, token_valido):
    res = client.get("/api/perfil", headers={
        "Authorization": f"Bearer {token_valido}"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data["mensaje"] == "Ruta protegida"


def test_join_server(client, token_valido, user_id):
    res = client.get("/api/join_server", headers={
        "Authorization": f"Bearer {token_valido}"
    })
    assert res.status_code == 200
    data = res.get_json()
    logging.info("Status code is 200")

    assert data["server"] in constants.CHAT_SERVERS_URL


def test_server_connection(client, token_valido, user_id):
    # Conect client to server
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
            data_package = {'command':'dummy'}
            msg = json.dumps(data_package)
            await websocket.send(msg)
            respuesta = await websocket.recv()
            logging.info(f"Servidor dice: {respuesta}")

            return respuesta

    asyncio.run(query_user_server())


# Send a Direct Message to Myself
def test_send_direct_message(client, token_valido, user_id):
    # Conect client to server
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
            data_package = {
                'command': 'new_message'
                ,'type': 'dm'
                ,'user_id': user_id
                ,'message': 'test message'
            }
            msg = json.dumps(data_package)
            await websocket.send(msg)
            respuesta = await websocket.recv()
            logging.info(f"Servidor dice: {respuesta}")

            return respuesta

    asyncio.run(query_user_server())
