import os
import sys

from flask import Flask

from config import Config
from .extensions import cors, db, migrate
from .models import seed_service_categories


def create_app(config_object=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, supports_credentials=True)

    from .routes.auth import auth_bp
    from .routes.pages import pages_bp
    from .routes.requests import requests_bp
    from .routes.sellers import sellers_bp
    from .routes.services import services_bp
    from .routes.uploads import uploads_bp
    from .routes.users import users_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(requests_bp)
    app.register_blueprint(sellers_bp)
    app.register_blueprint(uploads_bp)

    @app.cli.command("init-dev")
    def init_dev():
        """Create tables and seed default service categories."""
        db.create_all()
        seed_service_categories()
        print("Development database initialized.")

    is_migration_command = "db" in sys.argv
    if not is_migration_command:
        with app.app_context():
            db.create_all()
            seed_service_categories()

    return app
