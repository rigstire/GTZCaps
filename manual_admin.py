#!/usr/bin/env python
"""
One-time manual superuser creation for production
Run this ONCE locally, but it creates user in production DB
"""
import os
import django

# Force production environment
os.environ['VERCEL'] = '1'
os.environ['DATABASE_URL'] = 'your-production-database-url'  # Add your actual production DB URL

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MtzCaps.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Create superuser
username = input("Enter username (default: admin): ") or 'admin'
email = input("Enter email (default: admin@gtzcaps.com): ") or 'admin@gtzcaps.com'
password = input("Enter password: ")

try:
    user = User.objects.create_superuser(username, email, password)
    print(f"✅ Superuser '{username}' created successfully!")
    print("You can now login at /admin/")
except Exception as e:
    print(f"❌ Error: {e}") 