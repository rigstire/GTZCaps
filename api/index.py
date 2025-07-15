import os
import sys
import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MtzCaps.settings')

# Setup Django
django.setup()

# Import Django modules after setup
from django.core.management import execute_from_command_line
from django.contrib.staticfiles.handlers import StaticFilesHandler

# Collect static files and run migrations
print("Collecting static files...")
try:
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    print("Static files collected successfully!")
except Exception as e:
    print(f"Error collecting static files: {e}")

print("Running database migrations...")
try:
    execute_from_command_line(['manage.py', 'migrate', '--noinput'])
    print("Migrations completed successfully!")
except Exception as e:
    print(f"Error running migrations: {e}")

# Get the WSGI application
wsgi_application = get_wsgi_application()

# Wrap with StaticFilesHandler for serving static files
if os.getenv('VERCEL'):
    application = StaticFilesHandler(wsgi_application)
else:
    application = wsgi_application

# Export for Vercel (Vercel expects 'handler' or 'app')
handler = application
app = application
