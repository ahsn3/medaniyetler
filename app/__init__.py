import os

from flask import Flask, g, redirect, request, session, url_for

from app.extensions import db, login_manager
from app.models import User
from app.translations import DEFAULT_LANG, SUPPORTED_LANGS, t


def create_app():
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-in-production")
    db_url = os.environ.get("DATABASE_URL", "sqlite:////tmp/medaniyetler_finance.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    # Use psycopg v3 driver for PostgreSQL (works on Railway and modern Python)
    if db_url.startswith("postgresql://"):
        db_url = "postgresql+psycopg://" + db_url[len("postgresql://") :]
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = True

    if os.environ.get("FLASK_ENV") == "production" or os.environ.get("RAILWAY_ENVIRONMENT"):
        app.config["SESSION_COOKIE_SECURE"] = True
        app.config["SESSION_COOKIE_HTTPONLY"] = True
        app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
        app.config["REMEMBER_COOKIE_SECURE"] = True
        app.config["REMEMBER_COOKIE_HTTPONLY"] = True
        app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.before_request
    def pick_language():
        lang = request.args.get("lang")
        if lang in SUPPORTED_LANGS:
            session["lang"] = lang
        g.lang = session.get("lang", DEFAULT_LANG)
        if g.lang not in SUPPORTED_LANGS:
            g.lang = DEFAULT_LANG

    @app.context_processor
    def inject_i18n():
        lang = getattr(g, "lang", DEFAULT_LANG)

        def _(key: str) -> str:
            return t(lang, key)

        return {"_": _, "current_lang": lang}

    from app.auth import bp as auth_bp
    from app.finance import bp as finance_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(finance_bp)

    @app.route("/")
    def index():
        return redirect(url_for("finance.dashboard"))

    with app.app_context():
        db.create_all()

    return app
