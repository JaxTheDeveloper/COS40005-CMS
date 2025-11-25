# PostgreSQL Migration Guide - COS40005-CMS

## Executive Summary

Good news! Your Django CMS application is **already configured to use PostgreSQL**. This guide provides:
1. ✅ Current state assessment
2. 🔍 Best practices for production deployment
3. 📋 Migration checklist
4. 🔒 Security recommendations
5. 🚀 Deployment instructions

---

## 1. Current State Assessment

### Database Configuration
Your application uses PostgreSQL with the following configuration:

**Current Setup:**
- **Database Engine:** PostgreSQL (via `psycopg2-binary`)
- **Connection Method:** Environment variables
- **Default Container:** `cos40005_postgres`
- **Default Credentials:** 
  - User: `postgres`
  - Password: `password`
  - Database: `SwinCMS`
  - Port: `5432`

**Files Using PostgreSQL:**
- `config/settings/base.py` - Database configuration
- `docker-compose-dev.yaml` - PostgreSQL container setup
- `Dockerfile.dev` - Backend container with PostgreSQL support
- `requirements.txt` - Includes `psycopg2-binary`

### Current Models
The application has well-structured models across multiple apps:

| App | Purpose | Key Models |
|-----|---------|-----------|
| **users** | Authentication & Authorization | User, Role, UserRole |
| **academic** | Course & Unit Management | Course, Unit, SemesterOffering, UnitResource |
| **core** | Event, Attendance & Support | Event, Session, AttendanceRecord, Ticket, Notification |
| **enrollment** | Student Enrollment | (Enrollment-related models) |
| **social** | Social Features | (Social interaction models) |

---

## 2. Migration Tasks Status

### ✅ Already Completed

- [x] **PostgreSQL Driver**: `psycopg2-binary` in requirements.txt
- [x] **Database Configuration**: Set in `config/settings/base.py`
- [x] **Docker Setup**: PostgreSQL container in docker-compose-dev.yaml
- [x] **Environment Variables**: Properly configured for both dev and production
- [x] **Foreign Keys**: Properly configured with `on_delete` parameters
- [x] **Connection Pooling Ready**: Can be added easily

### ⚠️ Recommended Improvements

1. **Production Settings** - `config/settings/prod.py` is empty
2. **Connection Pooling** - Add psycopg2 connection pooling for production
3. **Database Backups** - Create backup strategy
4. **Migration Safety** - Add pre-production checks
5. **Environment Secrets** - Implement secure secret management
6. **SSL/TLS Connections** - For production databases

---

## 3. Implementation Guide

### Phase 1: Development Environment (Already Working)

The development environment is already configured correctly. To verify:

```bash
# Start development environment
docker-compose -f docker-compose-dev.yaml up -d

# Create migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Phase 2: Production Configuration

#### Step 2.1: Update Production Settings

Create/update `config/settings/prod.py`:

```python
from .base import *
import os

# Security settings for production
DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise ValueError("DJANGO_SECRET_KEY environment variable must be set")

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost').split(',')

# CORS - Restrict to specific origins in production
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')

# HTTPS & Security
SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True') == 'True'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database SSL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB'),
        'USER': os.environ.get('POSTGRES_USER'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'sslmode': 'require',
        },
        'ATOMIC_REQUESTS': True,
    }
}

# Connection pooling (optional but recommended)
# Install: pip install django-db-pool or django-db-gevent-psycopg2
# Then use: 'ENGINE': 'dj_db_conn_pool.backends.postgresql_psycopg2',

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
```

#### Step 2.2: Update Base Settings

Add connection pooling configuration to `config/settings/base.py`:

```python
# After the DATABASES definition, add:

# Connection pooling for better performance
if os.environ.get('USE_DB_POOL', 'False') == 'True':
    DATABASES['default'].update({
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'
        }
    })
```

#### Step 2.3: Environment Variables Template

Create `.env.example`:

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=config.settings.dev
DJANGO_SECRET_KEY=your-secret-key-change-in-production

# Database Configuration
POSTGRES_DB=SwinCMS
POSTGRES_USER=postgres
POSTGRES_PASSWORD=change-this-password
POSTGRES_HOST=cos40005_postgres
POSTGRES_PORT=5432

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Security
ALLOWED_HOSTS=localhost,127.0.0.1
SECURE_SSL_REDIRECT=False

# Optional: Connection Pooling
USE_DB_POOL=False
```

### Phase 3: Database Maintenance

#### Step 3.1: Backup Strategy

Create `scripts/backup-database.sh`:

```bash
#!/bin/bash

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.sql"

mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL database
docker exec cos40005_postgres pg_dump -U postgres -d SwinCMS > "$BACKUP_FILE"

echo "Database backed up to $BACKUP_FILE"

# Keep only last 30 backups
find "$BACKUP_DIR" -name "backup_*.sql" -type f -mtime +30 -delete
```

#### Step 3.2: Migration Best Practices

```bash
# Always back up before migrations
./scripts/backup-database.sh

# Create migration files
python manage.py makemigrations

# Preview migration SQL
python manage.py sqlmigrate appname migration_number

# Run migrations
python manage.py migrate

# If rollback needed
python manage.py migrate appname MIGRATION_NUMBER
```

### Phase 4: Performance Optimization

#### Step 4.1: Add Database Indexes

Create a migration with recommended indexes:

```python
# src/backend/users/migrations/0003_add_indexes.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0002_previous_migration'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=254, unique=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(choices=[...], db_index=True, max_length=20),
        ),
    ]
```

#### Step 4.2: Query Optimization

Review frequently used queries for `select_related()` and `prefetch_related()`:

```python
# Example: In views_api.py
from django.db.models import Prefetch

# Instead of:
users = User.objects.all()

# Use:
users = User.objects.select_related(
    'role'
).prefetch_related(
    Prefetch('events_attending'),
    Prefetch('tickets_assigned')
)
```

---

## 4. Security Recommendations

### 4.1 Database Access Control

```sql
-- Connect to PostgreSQL and run:
-- Create dedicated user for application
CREATE USER swin_cms WITH PASSWORD 'strong-password-here';
GRANT CONNECT ON DATABASE SwinCMS TO swin_cms;
GRANT USAGE ON SCHEMA public TO swin_cms;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO swin_cms;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO swin_cms;

-- Restrict postgres user
ALTER USER postgres WITH PASSWORD 'strong-password-here';
```

### 4.2 Environment Variables Security

- Never commit `.env` files
- Use secrets management tools (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault)
- Rotate credentials regularly
- Use strong passwords (min 32 characters)

### 4.3 Database Connection SSL

For production, enable SSL:

```python
# config/settings/prod.py
DATABASES = {
    'default': {
        ...
        'OPTIONS': {
            'sslmode': 'require',
            'sslcert': '/path/to/client-cert.pem',
            'sslkey': '/path/to/client-key.pem',
            'sslrootcert': '/path/to/ca-cert.pem',
        }
    }
}
```

---

## 5. Deployment Checklist

### Pre-Deployment

- [ ] Database backups configured
- [ ] Production settings file created
- [ ] Environment variables set up securely
- [ ] SSL/TLS certificates obtained
- [ ] Database user created with limited permissions
- [ ] Connection pooling configured (if needed)
- [ ] Load testing completed
- [ ] Security audit passed

### Deployment

- [ ] Run database migrations in staging first
- [ ] Verify all migrations applied successfully
- [ ] Check database connection from application
- [ ] Run full test suite
- [ ] Monitor application logs
- [ ] Verify data integrity

### Post-Deployment

- [ ] Monitor database performance
- [ ] Review slow query logs
- [ ] Set up automated backups
- [ ] Configure monitoring/alerting
- [ ] Document any changes
- [ ] Schedule regular maintenance

---

## 6. Docker Deployment

### Updated docker-compose for Production

Create `docker-compose-prod.yaml`:

```yaml
version: "3.9"
services:
  postgres:
    image: postgres:15-alpine
    container_name: cos40005_postgres_prod
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/backup-database.sh:/scripts/backup.sh:ro
    ports:
      - "5432:5432"
    networks:
      - backend
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.prod
    container_name: cos40005_backend_prod
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4"
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    env_file:
      - .env.prod
    ports:
      - "8000:8000"
    networks:
      - backend
    depends_on:
      postgres:
        condition: service_healthy
    restart: always

  nginx:
    image: nginx:alpine
    container_name: cos40005_nginx
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
    ports:
      - "80:80"
      - "443:443"
    networks:
      - backend
    depends_on:
      - backend
    restart: always

networks:
  backend:
    driver: bridge

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

### Production Dockerfile

Create `Dockerfile.prod`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

COPY . .

RUN python manage.py collectstatic --noinput --clear

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
```

---

## 7. Troubleshooting

### Common Issues & Solutions

#### Issue 1: "FATAL: Ident authentication failed for user 'postgres'"

**Solution:**
```bash
# Check pg_hba.conf
docker exec cos40005_postgres cat /var/lib/postgresql/data/pg_hba.conf

# Update authentication method
docker exec cos40005_postgres sudo sed -i 's/ident/md5/g' /var/lib/postgresql/data/pg_hba.conf
docker restart cos40005_postgres
```

#### Issue 2: "Django connection pooling not working"

**Solution:** Install connection pool package:
```bash
pip install django-db-gevent-psycopg2
# Update settings to use connection pool engine
```

#### Issue 3: "Migrations conflict"

**Solution:**
```bash
# Show migration status
python manage.py showmigrations

# Show migration graph
python manage.py showmigrations --graph

# Fake conflicting migration if needed
python manage.py migrate --fake-initial
```

#### Issue 4: "Database locked during migrations"

**Solution:**
```bash
# Terminate active connections
docker exec cos40005_postgres psql -U postgres -d SwinCMS -c \
  "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity 
   WHERE pg_stat_activity.datname = 'SwinCMS' AND pid <> pg_backend_pid();"

# Then retry migrations
python manage.py migrate
```

---

## 8. Performance Tuning

### PostgreSQL Configuration

```sql
-- Connect to PostgreSQL and optimize:
-- Increase work_mem for complex queries
ALTER DATABASE SwinCMS SET work_mem = '256MB';

-- Enable query optimization
ALTER DATABASE SwinCMS SET random_page_cost = 1.1;

-- Connection limits
ALTER SYSTEM SET max_connections = 200;
```

### Django Query Optimization

1. **Use `select_related()` for ForeignKey and OneToOneField**
2. **Use `prefetch_related()` for ManyToManyField and reverse relations**
3. **Use `.only()` and `.defer()` to limit fields**
4. **Use `.count()` instead of `len(queryset)`**
5. **Add database indexes on frequently filtered fields**

---

## 9. References

- [Django PostgreSQL Documentation](https://docs.djangoproject.com/en/4.2/ref/databases/#postgresql-notes)
- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [Psycopg2 Documentation](https://www.psycopg.org/psycopg2/docs/)
- [Django Migrations Documentation](https://docs.djangoproject.com/en/4.2/topics/migrations/)

---

## 10. Next Steps

1. **Immediate:** Review this guide and production settings
2. **Week 1:** Set up production environment and test migrations
3. **Week 2:** Implement connection pooling and caching
4. **Week 3:** Configure automated backups and monitoring
5. **Week 4:** Load testing and security audit

---

**Last Updated:** November 25, 2025  
**Status:** Ready for Implementation  
**Database Version:** PostgreSQL 12+
