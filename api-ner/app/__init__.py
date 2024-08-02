from flask import Flask
from app.routes import main
import os

def create_app():
    app = Flask(__name__)
    app.config['MODEL_DIR'] = os.path.join(app.root_path, './fine-tuned-model')
    app.register_blueprint(main)
    return app