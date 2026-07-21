# thinkx-system/citywalk/web-server/tests/legacy_ui_server.py
#
# Browser entry point for the original citywalk business application.

from __future__ import annotations

import collections
import collections.abc
import os
import sys
import types
from pathlib import Path


CITYWALK_ROOT = Path(__file__).resolve().parents[2]
LEGACY_APPLICATION = CITYWALK_ROOT / "legacy/www/server/application"
LEGACY_SCRIPTS = LEGACY_APPLICATION / "scripts"
LEGACY_VIEWS = LEGACY_APPLICATION / "views"
TEMPLATE_ROOT = LEGACY_VIEWS / "templates"
ECMA_ROOT = LEGACY_VIEWS / "src/ECMA"
IMAGE_ROOT = LEGACY_VIEWS / "img"
CSS_ROOT = CITYWALK_ROOT / "web-server/tests/.build/css"


def install_python_310_compatibility() -> None:
    collections.Mapping = collections.abc.Mapping
    collections.MutableMapping = collections.abc.MutableMapping
    collections.Iterable = collections.abc.Iterable

    dotenv = types.ModuleType("dotenv")
    dotenv.load_dotenv = lambda *args, **kwargs: None
    sys.modules["dotenv"] = dotenv

    mecab = types.ModuleType("MeCab")
    mecab.Tagger = lambda *args, **kwargs: None
    sys.modules["MeCab"] = mecab


def configure_legacy_runtime() -> None:
    os.environ.setdefault("ENV", "test")
    os.environ.setdefault("ENCRYPT_KEY", "citywalk-c0c-test-only")
    os.environ.setdefault("FLASK_SECRET_KEY", "citywalk-c0c-test-only")
    sys.path.insert(0, str(LEGACY_SCRIPTS))


def create_app():
    install_python_310_compatibility()
    configure_legacy_runtime()

    from flask import Flask, send_from_directory
    from views.business import blueprint_business

    app = Flask(__name__, template_folder=str(TEMPLATE_ROOT), static_folder=None)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.secret_key = "citywalk-c0c-test-only"
    app.register_blueprint(blueprint_business)

    @app.route("/healthcheck")
    def healthcheck() -> str:
        return "ok"

    @app.route("/")
    def index():
        from flask import render_template

        return render_template("index.html")

    @app.route("/css/<path:asset_path>")
    def css(asset_path: str):
        return send_from_directory(CSS_ROOT, asset_path)

    @app.route("/js/<path:asset_path>")
    def javascript(asset_path: str):
        return send_from_directory(ECMA_ROOT, asset_path)

    @app.route("/img/<path:asset_path>")
    def image(asset_path: str):
        return send_from_directory(IMAGE_ROOT, asset_path)

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(CITYWALK_ROOT / "legacy/www", "favicon.ico")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=4173, debug=False)
