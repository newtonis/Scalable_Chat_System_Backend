import argparse
import logging

from flask import Flask
from routes.api import protected_bp
from routes.auth import auth_bp
from utils import constants

app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "1234"  # TODO: Colocar clave como un secret

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(protected_bp, url_prefix="/api")


@app.route("/", methods=["GET"])
def index():
    return {"mensaje": "Flask API is running", "status": "ok"}


def start_coordinator():
    parser = argparse.ArgumentParser(description="Coordinator Api")
    parser.add_argument("kv_store_host", type=str, help="Kv store host", default="localhost")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",  # Clean disign for console
    )

    args = parser.parse_args()

    app.config["KV_STORE_URL"] = constants.KV_STORE_URL.format(host=args.kv_store_host)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",  # Clean design for console
    )
    app.run(host="0.0.0.0", debug=True, port=5000)
