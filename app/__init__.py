from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail

db = db_instance = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
mail = Mail()

def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Blueprinty
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/auth")

    from app.student import student_bp
    app.register_blueprint(student_bp, url_prefix="/student")

    from app.opiekun.routes import opiekun_bp
    app.register_blueprint(opiekun_bp, url_prefix="/opiekun")

    from app.dziekanat.routes import dziekanat_bp
    app.register_blueprint(dziekanat_bp, url_prefix="/dziekanat")

    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # REST API
    from app.api import api_bp
    app.register_blueprint(api_bp)

    # Utwórz tabele
    with app.app_context():
        from app.models.user import User
        from app.models.internship import Internship, LearningOutcome, DiaryEntry
        db.create_all()
        # Dodaj kolumny jeśli nie istnieją (SQLite nie obsługuje IF NOT EXISTS w ADD COLUMN)
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE users ADD COLUMN student_index VARCHAR(20)"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        try:
            from sqlalchemy import text
            db.session.execute(text("ALTER TABLE internships ADD COLUMN rejection_reason TEXT"))
            db.session.commit()
        except Exception:
            db.session.rollback()
        # Seed required attachments if missing
        try:
            from app.models import Attachment, REQUIRED_ATTACHMENTS, ATTACHMENT_AUDIENCE
            for name in REQUIRED_ATTACHMENTS:
                exists = Attachment.query.filter_by(name=name).first()
                if not exists:
                    audience = ATTACHMENT_AUDIENCE.get(name, 'all')
                    a = Attachment(name=name, filename=None, description=None, audience=audience, required=True)
                    db.session.add(a)
            db.session.commit()
            try:
                print("[app.create_app] attachments in DB:", Attachment.query.count())
            except Exception:
                pass
        except Exception as _e:
            print("[app.create_app] seeding attachments failed:", _e)

    # Root redirect -> login
    from flask import redirect, url_for

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    return app