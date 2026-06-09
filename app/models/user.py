from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    full_name     = db.Column(db.String(255))
    first_name    = db.Column(db.String(128))
    last_name     = db.Column(db.String(128))
    student_index = db.Column(db.String(20), nullable=True)   # numer albumu
    auth_provider = db.Column(db.String(50), default="local")
    external_id   = db.Column(db.String(255), unique=True, nullable=True)
    role          = db.Column(db.String(50), nullable=False, default="pending")
    is_active     = db.Column(db.Boolean, default=True)
    password_hash = db.Column(db.String(256))

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email} [{self.role}]>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))