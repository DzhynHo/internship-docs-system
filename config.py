import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
    MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
    MICROSOFT_TENANT_ID = os.getenv("MICROSOFT_TENANT_ID")
    MICROSOFT_REDIRECT_URI = os.getenv("MICROSOFT_REDIRECT_URI")

    STUDENT_DOMAIN = os.getenv("STUDENT_DOMAIN", "student.uczelnia.pl")
    STAFF_DOMAIN = os.getenv("STAFF_DOMAIN", "uczelnia.pl")
    
    # Session cookie settings suitable for local development
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") in ["True", "true", "1"]
    SESSION_COOKIE_HTTPONLY = True
    
    # Email Configuration
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") in ["True", "true", "1"]
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "noreply@uczelnia.pl")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", ("System Praktyk", "noreply@uczelnia.pl"))
    
    # Application Settings
    APP_NAME = "System Praktyk Zawodowych"
    APP_VERSION = "1.0.0"
    
    # Upload settings
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "instance/uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png'}
    
    # PDF Settings
    WEASYPRINT_FONT_CONFIG = None  # Use system fonts