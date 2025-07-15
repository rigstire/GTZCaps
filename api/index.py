# api/index.py
import os
import sys
from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MtzCaps.settings")

# Set environment variables for production
os.environ.setdefault("VERCEL", "1")

# Initialize Django
application = get_wsgi_application()

# For Vercel compatibility
app = application

def handler(environ, start_response):
    return app(environ, start_response)
