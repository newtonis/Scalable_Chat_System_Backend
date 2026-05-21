from flask import Flask
from routes.api import api_bp

app = Flask(__name__)

app.register_blueprint(api_bp, url_prefix="/api")


@app.get("/")
def index():
    return {"mensaje": "Flask id generator API is running", "status": "ok"}


def start_id_generator():
    app.run(debug=True, port=5002)

