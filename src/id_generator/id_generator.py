import argparse
import logging

from flask import Flask
from routes.api import api_bp

app = Flask(__name__)

app.register_blueprint(api_bp, url_prefix="/api")


@app.get("/")
def index():
    return {"mensaje": "Flask id generator API is running", "status": "ok"}


def start_id_generator():
    parser = argparse.ArgumentParser(description="Id generator Api")
    parser.add_argument("postgres_host", type=str, help="postgres host", default="localhost")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",  # Clean disign for console
    )

    args = parser.parse_args()

    app.config["POSTGRES_HOST"] = args.postgres_host

    app.run(host="0.0.0.0", debug=True, port=5002)
