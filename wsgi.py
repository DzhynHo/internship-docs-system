import sys
import os

# Dodaj sciezke projektu
project_home = '/home/TWOJA_NAZWA/internship-docs-system'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Wczytaj zmienne srodowiskowe z .env jesli istnieje
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

from app import create_app
application = create_app()
