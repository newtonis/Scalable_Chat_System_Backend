from flask import Flask
from routes.api import api_bp
import argparse

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "1234"  # TODO: Colocar clave como un secret

app.register_blueprint(api_bp, url_prefix="/api")


@app.get("/")
def index():
    return {"mensaje": "Flask API is running", "status": "ok"}


def start_kv_store():
    parser = argparse.ArgumentParser(description="KV Store API")
    parser.add_argument("redis_host", type=str, help="redis host", default="localhost")

    args = parser.parse_args()

    app.config["REDIS_HOST"] = args.redis_host

    app.run(host="0.0.0.0", debug=True, port=5001)
