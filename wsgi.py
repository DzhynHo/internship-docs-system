import sys
import os

# Sciezka projektu
project_home = '/home/epraktyki/internship-docs-system'

# Dodaj venv site-packages do path (zanim cokolwiek importujemy)
venv_site = os.path.join(project_home, 'venv', 'lib', 'python3.10', 'site-packages')
if venv_site not in sys.path:
    sys.path.insert(0, venv_site)

if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Wczytaj .env jesli istnieje
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_home, '.env'))
except ImportError:
    pass

from app import create_app
application = create_app()
