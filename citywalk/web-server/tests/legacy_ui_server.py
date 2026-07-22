# thinkx-system/citywalk/web-server/tests/legacy_ui_server.py
#
# Browser entry point for the original citywalk business application.

from __future__ import annotations

import collections
import collections.abc
import os
import re
import sys
import types
from pathlib import Path


CITYWALK_ROOT = Path(__file__).resolve().parents[2]
LEGACY_APPLICATION = CITYWALK_ROOT / "legacy/www/server/application"
LEGACY_SCRIPTS = LEGACY_APPLICATION / "scripts"
LEGACY_VIEWS = LEGACY_APPLICATION / "views"
TEMPLATE_ROOT = LEGACY_VIEWS / "templates"
IMAGE_ROOT = LEGACY_VIEWS / "img"
CSS_ROOT = CITYWALK_ROOT / "web-server/tests/.build/css"
JAVASCRIPT_ROOT = CITYWALK_ROOT / "web-server/tests/.build/js"
GOOGLE_MAPS_SCRIPT_PATTERN = re.compile(
    rb"(https://maps\.googleapis\.com/maps/api/js\?[^\"']*?\bkey=)[^&\"']+"
)


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


def demo_contents() -> list[dict]:
    shared = {
        "media_type": "audio",
        "language": "en",
        "organization_id": None,
        "created_member_id": "000000000000000000000001",
        "latest_edit_member_id": "000000000000000000000001",
        "deleted": False,
    }
    return [
        {
            **shared,
            "_id": "000000000000000000000101",
            "index": 1,
            "lat": 46.953976,
            "lon": 7.456123,
            "label": "Giza Pyramid",
            "title": "The secret of Giza Pyramid",
            "text": "The Great Pyramid of Giza is the oldest pyramids in the Giza pyramid complex",
            "target": 0,
            "radius": 5,
        },
        {
            **shared,
            "_id": "000000000000000000000102",
            "index": 2,
            "lat": 46.933176,
            "lon": 7.440143,
            "label": "Mona Lisa",
            "title": "Mona Lisa Title and subject",
            "text": (
                "The title of the painting, which is known in English as Mona Lisa, "
                "comes from a description by Renaissance art historian Giorgio Vasari, "
                "who wrote Leonardo undertook to paint the portrait of Mona Lisa."
            ),
        },
        {
            **shared,
            "_id": "000000000000000000000103",
            "index": 3,
            "lat": 46.943956,
            "lon": 7.426124,
            "label": "Renaissance",
            "title": "Social and political structures in Italy",
            "text": (
                "The unique political structures of late Middle Ages Italy have led some to theorize "
                "that its unusual social climate allowed the emergence of a rare cultural efflorescence."
            ),
            "target": 0,
            "radius": 5,
        },
        {
            **shared,
            "_id": "000000000000000000000104",
            "index": 4,
            "lat": 46.943416,
            "lon": 7.439110,
            "label": "ルネサンス",
            "title": "構成的な明暗法",
            "text": (
                "暗い物体が、単一でしばしば目に見えない光源から放たれる一条の光によって劇的に照らされるという、"
                "この構成的な明暗法を発展させた。とくにカラヴァッジオは、劇的な明暗法が支配的な技法となる"
                "テネブリズムの発達に重大な貢献をした。"
            ),
        },
    ]


def create_app():
    install_python_310_compatibility()
    configure_legacy_runtime()

    from flask import Flask, jsonify, send_from_directory
    from libcommon.enumlocale import EnumLocale
    from views.business import blueprint_business

    # The pinned legacy snapshot omitted this decorator; restore its documented API.
    EnumLocale.is_valid_value = classmethod(EnumLocale.is_valid_value)

    app = Flask(__name__, template_folder=str(TEMPLATE_ROOT), static_folder=None)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.secret_key = "citywalk-c0c-test-only"
    app.register_blueprint(blueprint_business)

    @app.after_request
    def inject_google_maps_browser_key(response):
        browser_key = os.environ.get("CITYWALK_GOOGLE_MAPS_API_KEY")
        if browser_key and response.content_type.startswith("text/html"):
            response.set_data(
                GOOGLE_MAPS_SCRIPT_PATTERN.sub(
                    lambda match: match.group(1) + browser_key.encode(),
                    response.get_data(),
                )
            )
        return response

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
        response = send_from_directory(JAVASCRIPT_ROOT, asset_path)
        if asset_path == "business/appconfig.js":
            response.direct_passthrough = False
            response.set_data(
                response.get_data().replace(
                    b"http://citywalkservers.localhost:8000",
                    b"http://127.0.0.1:4173",
                )
            )
        return response

    @app.route("/demo/1/contents/guide/list")
    def contents_guide_list_demo_1():
        return jsonify(
            {
                "saved_data": None,
                "contents": demo_contents(),
                "success": {"code": 200, "message": "contents successfully fetched."},
            }
        )

    @app.route("/img/<path:asset_path>")
    def image(asset_path: str):
        return send_from_directory(IMAGE_ROOT, asset_path)

    @app.route("/favicon.ico")
    def favicon():
        return send_from_directory(CITYWALK_ROOT / "legacy/www", "favicon.ico")

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=4173, debug=False)
