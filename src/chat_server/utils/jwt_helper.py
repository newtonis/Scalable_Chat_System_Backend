import jwt
from urllib.parse import urlparse, parse_qs
from utils.config import config


def get_user_data_from_path(path) -> (int, str):
    # 1.Url Parse
    print(path)
    url_parseada = urlparse(path)
    parametros = parse_qs(url_parseada.query)

    # 2. Get token from url parameter
    token = None
    print(parametros)
    token = parametros.get("token")
    print(token[0])

    if not token:
        return 0, {"error": "no token received"}

    try:
        payload = jwt.decode(token[0], config["JWT_SECRET_KEY"], algorithms=["HS256"])
        user_id = payload["sub"]
    except jwt.ExpiredSignatureError:
        print("User has sent expired token")
        return 0, {"error": "expired token"}
    except jwt.InvalidTokenError:
        print("User has sent invalid token")
        return 0, {"error": "invalid token"}

    return 1, {"user_id": user_id, "token": token[0]}
