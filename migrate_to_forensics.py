#!/usr/bin/env python
"""
Migration script to move data from old apps structure to new forensics app.
Only run this if you have existing data in the old structure.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'traceflow.settings')
django.setup()

def migrate_data():
    """
    Migrate data from old apps to new forensics app.
    This is only needed if you have existing data from the old structure.
    """
    print("This migration script is for reference only.")
    print("Since we're restructuring before production, no data migration is needed.")
    print("\nNew installation steps:")
    print("1. Delete db.sqlite3 if it exists")
    print("2. Run: python manage.py makemigrations")
    print("3. Run: python manage.py migrate")
    print("4. Run: python manage.py generate_fake_data")

if __name__ == '__main__':
    migrate_data()
