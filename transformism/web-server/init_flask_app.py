from flask import Flask, render_template, request, g, jsonify
from jinja2 import ChoiceLoader, FileSystemLoader

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'FLASK_APP_SECRET_KEY',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

app = Flask(__name__)
app.jinja_loader = ChoiceLoader([
    FileSystemLoader(['views/templates', 'mails/templates']),
])
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = Config.FLASK_APP_SECRET_KEY