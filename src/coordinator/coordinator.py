from flask import Flask
from routes.auth import auth_bp
from routes.api import protected_bp
import logging


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "1234"  # TODO: Colocar clave como un secret

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(protected_bp, url_prefix="/api")


@app.route("/", methods=["GET"])
def index():
    return {"mensaje": "Flask API is running", "status": "ok"}


def start_coordinator():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"  # Clean disign for console
    )
    app.run(debug=True, port=5000)

