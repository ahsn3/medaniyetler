import os
from decimal import Decimal, InvalidOperation

import click
from flask import Flask, g, redirect, request, session, url_for

from app.extensions import db, login_manager
from app.models import Transaction, User
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

    @app.template_filter("fmt_amount")
    def format_amount(value) -> str:
        """Format numeric amounts with thousand separators and 2 decimals."""
        if value is None:
            return "0.00"
        try:
            number = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return "0.00"
        return f"{number:,.2f}"

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

    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables."""
        db.create_all()
        click.echo("Database tables created.")

    @app.cli.command("create-user")
    @click.option("--username", prompt=True, help="Username for login.")
    @click.option("--email", prompt=True, help="User email.")
    @click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True)
    def create_user_command(username: str, email: str, password: str):
        """Create a user account from CLI."""
        normalized_username = username.strip()
        normalized_email = email.strip().lower()
        existing = User.query.filter(
            (User.username == normalized_username) | (User.email == normalized_email)
        ).first()
        if existing:
            click.echo("User with this username or email already exists.")
            return
        user = User(username=normalized_username, email=normalized_email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f"User created: {normalized_username}")

    @app.cli.command("seed-demo-data")
    @click.option("--username", default="demo", show_default=True, help="Demo username.")
    @click.option(
        "--email",
        default="demo@example.com",
        show_default=True,
        help="Demo user email.",
    )
    @click.option(
        "--password",
        default="demo12345",
        show_default=True,
        help="Demo user password.",
    )
    def seed_demo_data_command(username: str, email: str, password: str):
        """Create one demo user and sample finance transactions."""
        normalized_username = username.strip()
        normalized_email = email.strip().lower()
        user = User.query.filter(
            (User.username == normalized_username) | (User.email == normalized_email)
        ).first()
        if not user:
            user = User(username=normalized_username, email=normalized_email)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

        existing_count = Transaction.query.filter_by(user_id=user.id).count()
        if existing_count == 0:
            seed_rows = [
                Transaction(
                    user_id=user.id,
                    kind="income",
                    amount=5000,
                    description="Initial donation",
                ),
                Transaction(
                    user_id=user.id,
                    kind="expense",
                    amount=800,
                    description="Office supplies",
                ),
                Transaction(
                    user_id=user.id,
                    kind="expense",
                    amount=1200,
                    description="Program support",
                ),
            ]
            db.session.add_all(seed_rows)
        db.session.commit()
        click.echo(f"Demo data is ready for user: {normalized_username}")

    @app.route("/")
    def index():
        return redirect(url_for("finance.dashboard"))

    with app.app_context():
        db.create_all()

    return app
