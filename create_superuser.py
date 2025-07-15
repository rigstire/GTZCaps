#!/usr/bin/env python
"""
Script to create a Django superuser for production
Run this once after deployment to create admin access
"""
import os
import django
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MtzCaps.settings')
django.setup()

User = get_user_model()

def create_superuser():
    # Check if superuser already exists
    if User.objects.filter(is_superuser=True).exists():
        print("Superuser already exists!")
        existing_superuser = User.objects.filter(is_superuser=True).first()
        print(f"Existing superuser: {existing_superuser.username}")
        return
    
    # Create superuser with environment variables
    username = os.getenv('ADMIN_USERNAME', 'admin')
    email = os.getenv('ADMIN_EMAIL', 'admin@gtzcaps.com')
    password = os.getenv('ADMIN_PASSWORD', 'gtzcaps_admin_2024')  # Change this!
    
    try:
        superuser = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f"✅ Superuser created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Login at: /admin/")
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

if __name__ == "__main__":
    create_superuser() 