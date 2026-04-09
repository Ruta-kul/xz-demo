"""Flask web dashboard for XZ-Bot."""
from pathlib import Path

from flask import Flask


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    app.config["SECRET_KEY"] = "xz-bot-educational-demo"

    from xz_bot.web.routes import bp
    app.register_blueprint(bp)

    return app


def run_web(port: int = 5000, debug: bool = False):
    app = create_app()
    app.run(host="0.0.0.0", port=port, debug=debug)
