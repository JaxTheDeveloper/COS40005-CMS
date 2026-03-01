#!/usr/bin/env python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')
django.setup()

from django.db import connection
from django.db.migrations.loader import MigrationLoader

# Check migration status
loader = MigrationLoader(None, ignore_no_migrations=True)
print("=== Applied Migrations ===")
for app, migration_name in loader.applied_migrations:
    if app in ['academic', 'core']:
        print(f"{app}: {migration_name}")

print("\n=== Unapplied Migrations ===")
for app, migration_name in loader.graph.leaf_nodes():
    if app in ['academic', 'core']:
        if (app, migration_name) not in loader.applied_migrations:
            print(f"{app}: {migration_name}")

# Check if tables exist
print("\n=== Database Tables Check ===")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema='public' AND table_name IN 
        ('academic_intake', 'core_event', 'core_event_target_students', 'core_event_target_offerings', 'core_event_target_intakes')
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    if tables:
        print("Tables found:")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("No new tables found")

# Check columns on core_event
print("\n=== core_event columns ===")
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='core_event'
        ORDER BY ordinal_position
    """)
    cols = cursor.fetchall()
    for col in cols:
        print(f"  - {col[0]}")
