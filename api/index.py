# api/index.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MtzCaps.settings")  # change this!

app = get_wsgi_application()

def handler(environ, start_response):
    return app(environ, start_response)
