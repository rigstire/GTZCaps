import os
import sys
import django
from django.core.wsgi import get_wsgi_application

# Add the project directory to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Set the Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MtzCaps.settings")

# Set environment variables for production
os.environ.setdefault("VERCEL", "1")

# Run database migrations on startup
def run_migrations():
    try:
        from django.core.management import execute_from_command_line
        print("Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("Migrations completed successfully!")
    except Exception as e:
        print(f"Migration error: {e}")

# Initialize Django
try:
    django.setup()
    run_migrations()
    application = get_wsgi_application()
    print("Django application initialized successfully!")
except Exception as e:
    print(f"Django initialization error: {e}")
    import traceback
    traceback.print_exc()
    raise

# Export for Vercel
app = application
