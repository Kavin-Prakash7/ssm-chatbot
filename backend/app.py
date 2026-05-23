
from flask import Flask
from flask_cors import CORS

from backend.routes.chatbot_routes import chatbot_bp


def create_app():
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates",
    )
    CORS(app)
    app.register_blueprint(chatbot_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
