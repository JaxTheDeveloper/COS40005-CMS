import os
import sys

# Ensure we run from project root
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# Choose settings module - try dev, then base
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.dev')

try:
    import django
    django.setup()
    from django.db import connection
except Exception as e:
    print('Failed to set up Django environment:', e)
    sys.exit(2)

print('Using Django settings module:', os.environ.get('DJANGO_SETTINGS_MODULE'))

try:
    tables = connection.introspection.table_names()
except Exception as e:
    print('Error obtaining table list from DB:', e)
    sys.exit(3)

print('\nFound tables (%d):' % len(tables))
for t in sorted(tables):
    print(' -', t)

print('\nSchema detail:')
for t in sorted(tables):
    print('\n--', t)
    try:
        with connection.cursor() as cursor:
            desc = connection.introspection.get_table_description(cursor, t)
            for col in desc:
                # col has attributes: name, type_code, display_size, internal_size, precision, scale, null_ok
                name = getattr(col, 'name', col[0])
                type_code = getattr(col, 'type_code', None)
                null_ok = getattr(col, 'null_ok', None)
                print(f'  {name} | type_code={type_code} | null_ok={null_ok}')
            # indexes/constraints
            try:
                rels = connection.introspection.get_relations(cursor, t)
                if rels:
                    print('  Relations:', rels)
            except Exception:
                pass
    except Exception as e:
        print('  Error describing table:', e)

print('\nIntrospection complete.')
