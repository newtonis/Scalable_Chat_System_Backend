import pytest
import jwt
import datetime
from app import app
from utils import users


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────

@pytest.fixture
def client():
    # Test client with clean dabase on each test
    app.config["TESTING"] = True
    app.config["JWT_SECRET_KEY"] = "1234"
    users.users_db.clear()

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


# ──────────────────────────────────────────────
# Tests: /auth/register
# ──────────────────────────────────────────────

class TestRegister:

    def test_registro_exitoso(self, client):
        res = client.post("/auth/register", json={
            "email": "nuevo@example.com",
            "constraseña": "abcd"
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["mensaje"] == "Usuario registrado correctamente"
        assert "id" in data

    def test_registro_sin_email(self, client):
        res = client.post("/auth/register", json={"password": "1234"})
        assert res.status_code == 400
        assert "error" in res.get_json()

    def test_registro_sin_password(self, client):
        res = client.post("/auth/register", json={"email": "a@a.com"})
        assert res.status_code == 400
        assert "error" in res.get_json()

    def test_registro_body_vacio(self, client):
        res = client.post("/auth/register", json={})
        assert res.status_code == 400

    def test_registro_sin_json(self, client):
        res = client.post("/auth/register", data="no-es-json",
                          content_type="text/plain")
        assert res.status_code == 400

    def test_registro_usuario_duplicado(self, client, usuario_registrado):
        res = client.post("/auth/register", json=usuario_registrado)
        assert res.status_code == 409
        assert res.get_json()["error"] == "El usuario ya existe"

    def test_registro_ids_incrementales(self, client):
        res1 = client.post("/auth/register", json={
            "email": "uno@example.com", "password": "1"
        })
        res2 = client.post("/auth/register", json={
            "email": "dos@example.com", "password": "2"
        })
        assert res1.get_json()["id"] == 1
        assert res2.get_json()["id"] == 2


# ──────────────────────────────────────────────
# Tests: /auth/login
# ──────────────────────────────────────────────

class TestLogin:

    def test_login_exitoso(self, client, usuario_registrado):
        res = client.post("/auth/login", json=usuario_registrado)
        assert res.status_code == 200
        assert "token" in res.get_json()

    def test_login_retorna_jwt_valido(self, client, usuario_registrado):
        res = client.post("/auth/login", json=usuario_registrado)
        token = res.get_json()["token"]
        payload = jwt.decode(
            token,
            app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"]
        )
        assert "sub" in payload
        assert "exp" in payload

    def test_login_password_incorrecta(self, client, usuario_registrado):
        res = client.post("/auth/login", json={
            "email": usuario_registrado["email"],
            "password": "incorrecta"
        })
        assert res.status_code == 401
        assert res.get_json()["error"] == "Credenciales inválidas"

    def test_login_usuario_inexistente(self, client):
        res = client.post("/auth/login", json={
            "email": "noexiste@example.com",
            "password": "1234"
        })
        assert res.status_code == 401

    def test_login_sin_email(self, client):
        res = client.post("/auth/login", json={"password": "1234"})
        assert res.status_code == 400

    def test_login_sin_password(self, client):
        res = client.post("/auth/login", json={"email": "a@a.com"})
        assert res.status_code == 400

    def test_login_body_vacio(self, client):
        res = client.post("/auth/login", json={})
        assert res.status_code == 400


# ──────────────────────────────────────────────
# Tests: /api/perfil (ruta protegida)
# ──────────────────────────────────────────────

class TestRutaProtegida:

    def test_acceso_con_token_valido(self, client, token_valido):
        res = client.get("/api/perfil", headers={
            "Authorization": f"Bearer {token_valido}"
        })
        assert res.status_code == 200
        assert "user_id" in res.get_json()

    def test_acceso_sin_token(self, client):
        res = client.get("/api/perfil")
        assert res.status_code == 401
        assert res.get_json()["error"] == "Token requerido"

    def test_acceso_token_invalido(self, client):
        res = client.get("/api/perfil", headers={
            "Authorization": "Bearer token.falso.invalido"
        })
        assert res.status_code == 401
        assert res.get_json()["error"] == "Token inválido"

    def test_acceso_token_expirado(self, client):
        payload = {
            "sub": 1,
            "iat": datetime.datetime.utcnow() - datetime.timedelta(hours=48),
            "exp": datetime.datetime.utcnow() - datetime.timedelta(hours=24),
        }
        token_expirado = jwt.encode(
            payload,
            app.config["JWT_SECRET_KEY"],
            algorithm="HS256"
        )
        res = client.get("/api/perfil", headers={
            "Authorization": f"Bearer {token_expirado}"
        })
        assert res.status_code == 401
        assert res.get_json()["error"] == "Token expirado"

    def test_acceso_sin_bearer_prefix(self, client, token_valido):
        res = client.get("/api/perfil", headers={
            "Authorization": token_valido  # Sin "Bearer "
        })
        assert res.status_code == 401

    def test_token_contiene_user_id_correcto(self, client, usuario_registrado):
        # Registrar y loguear
        res_login = client.post("/auth/login", json=usuario_registrado)
        token = res_login.get_json()["token"]

        res_perfil = client.get("/api/perfil", headers={
            "Authorization": f"Bearer {token}"
        })
        assert res_perfil.status_code == 200
        assert res_perfil.get_json()["user_id"] == 1
