from flask import Flask
from src.api import register_blueprints


app = Flask(__name__)
register_blueprints(app)
