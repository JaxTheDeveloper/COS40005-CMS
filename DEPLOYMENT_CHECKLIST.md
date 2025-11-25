# PostgreSQL Migration Checklist

**Project:** COS40005-CMS  
**Date Started:** November 25, 2025  
**Target Database:** PostgreSQL 12+

---

## Phase 1: Pre-Migration Preparation

### Configuration Review
- [x] Review current database configuration in `config/settings/base.py`
- [x] Verify PostgreSQL is the configured database engine
- [x] Check environment variable setup
- [x] Review Docker Compose configuration
- [x] Verify psycopg2-binary is in requirements.txt

### Documentation & Planning
- [x] Create comprehensive migration guide (`POSTGRESQL_MIGRATION_GUIDE.md`)
- [x] Create implementation summary (`IMPLEMENTATION_SUMMARY.md`)
- [x] Create code review analysis (`CODE_REVIEW.md`)
- [x] Create this checklist
- [x] Document all recommended changes

### Security Audit
- [x] Review authentication mechanisms
- [x] Check password handling
- [x] Verify encryption strategies
- [x] Review CORS settings
- [x] Plan SSL/TLS implementation

---

## Phase 2: Development Environment Setup

### Local Development
- [ ] Copy `.env.example.dev` to `.env.dev`
- [ ] Start Docker containers: `docker-compose -f docker-compose-dev.yaml up -d`
- [ ] Verify PostgreSQL container is running: `docker ps`
- [ ] Check container logs: `docker logs cos40005_postgres`
- [ ] Test database connection

### Database Initialization
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Verify migrations applied: `python manage.py showmigrations`
- [ ] Load initial data if needed: `python manage.py loaddata`
- [ ] Test application startup

### Testing
- [ ] Test user registration
- [ ] Test authentication endpoints
- [ ] Test API endpoints
- [ ] Verify static file serving
- [ ] Check media file uploads
- [ ] Test database queries

---

## Phase 3: Production Environment Configuration

### Environment Setup
- [ ] Copy `.env.example.prod` to `.env.prod`
- [ ] Set `DJANGO_SECRET_KEY` (32+ characters)
- [ ] Set `POSTGRES_PASSWORD` (strong password)
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Configure `CORS_ALLOWED_ORIGINS`
- [ ] Set email configuration if needed
- [ ] Document all environment variables

### Security Configuration
- [ ] Obtain SSL/TLS certificates (Let's Encrypt or provider)
- [ ] Place certificates in designated directory
- [ ] Generate strong database passwords
- [ ] Create dedicated database user
- [ ] Configure firewall rules
- [ ] Set up security headers in nginx.conf

### Database Preparation
- [ ] Plan backup strategy
- [ ] Review backup script: `scripts/backup-database.sh`
- [ ] Review restore script: `scripts/restore-database.sh`
- [ ] Create backups directory
- [ ] Test backup process locally
- [ ] Document backup retention policy

---

## Phase 4: Docker Production Setup

### Image Building
- [ ] Review `Dockerfile.prod`
- [ ] Verify all dependencies are correct
- [ ] Test image build locally
- [ ] Verify gunicorn configuration
- [ ] Check Python version compatibility
- [ ] Review layer optimization

### Docker Compose Configuration
- [ ] Review `docker-compose-prod.yaml`
- [ ] Verify all service configurations
- [ ] Check volume mounts
- [ ] Verify health checks
- [ ] Review restart policies
- [ ] Check networking configuration
- [ ] Verify logging configuration

### Nginx Configuration
- [ ] Review `nginx.conf`
- [ ] Verify SSL settings
- [ ] Check rate limiting configuration
- [ ] Review security headers
- [ ] Verify static file paths
- [ ] Check proxy settings
- [ ] Test gzip compression

---

## Phase 5: Staging Deployment

### Pre-Deployment
- [ ] Create staging environment copy
- [ ] Copy production database to staging (optional)
- [ ] Set up staging environment variables
- [ ] Verify all required files are present
- [ ] Make scripts executable: `chmod +x scripts/*.sh`
- [ ] Create logs directory

### Deployment
- [ ] Run deployment script: `./scripts/deploy.sh`
- [ ] Wait for database initialization
- [ ] Verify containers are running
- [ ] Check container logs for errors
- [ ] Verify database migrations ran successfully

### Testing in Staging
- [ ] Test user registration/login
- [ ] Test all API endpoints
- [ ] Test file uploads
- [ ] Verify email functionality
- [ ] Check static file serving
- [ ] Verify CORS headers
- [ ] Test with production-like data volume
- [ ] Run performance tests
- [ ] Check database performance

### Verification
- [ ] Access application via HTTPS
- [ ] Verify SSL certificate validity
- [ ] Check security headers with curl:
  ```bash
  curl -I https://staging-url
  ```
- [ ] Verify rate limiting works
- [ ] Test error pages (404, 500)
- [ ] Check logging
- [ ] Review application logs for errors

---

## Phase 6: Data Migration (if needed)

### Data Inventory
- [ ] Identify all data sources
- [ ] Plan data validation
- [ ] Create data backup
- [ ] Document data transformation rules

### Data Transfer
- [ ] Export existing data (if migrating from other DB)
- [ ] Transform data as needed
- [ ] Import data to PostgreSQL
- [ ] Verify data integrity
- [ ] Run consistency checks
- [ ] Update any sequence numbers

### Post-Migration
- [ ] Verify all records transferred
- [ ] Check referential integrity
- [ ] Verify file uploads still accessible
- [ ] Test complex queries

---

## Phase 7: Production Deployment

### Final Pre-Deployment
- [ ] Final backup of all data
- [ ] Notify users of maintenance window
- [ ] Prepare rollback plan
- [ ] Verify all team members know deployment steps
- [ ] Document any custom configurations
- [ ] Have SSH access ready

### Deployment
- [ ] Set application to maintenance mode (if available)
- [ ] Run final backup: `./scripts/backup-database.sh`
- [ ] Run deployment script: `./scripts/deploy.sh`
- [ ] Wait for all services to start
- [ ] Verify database migrations completed
- [ ] Check application health endpoint

### Immediate Post-Deployment
- [ ] Monitor application logs closely
- [ ] Check error tracking/logging
- [ ] Monitor database performance
- [ ] Verify API responses
- [ ] Test critical user journeys
- [ ] Monitor server resources (CPU, memory, disk)
- [ ] Check database connections

### User Communication
- [ ] Announce service is online
- [ ] Monitor user reports
- [ ] Respond to issues quickly
- [ ] Provide status updates if issues arise

---

## Phase 8: Post-Deployment Optimization

### Performance Monitoring
- [ ] Set up application monitoring (New Relic, DataDog, etc.)
- [ ] Monitor database query performance
- [ ] Check slow query logs
- [ ] Review application error rates
- [ ] Monitor resource utilization
- [ ] Set up alerts for critical issues

### Database Optimization
- [ ] Analyze query plans for slow queries
- [ ] Add indexes if needed based on metrics
- [ ] Optimize connection pooling settings
- [ ] Review PostgreSQL configuration
- [ ] Set up automated ANALYZE jobs
- [ ] Monitor table bloat

### Infrastructure Optimization
- [ ] Review nginx access logs
- [ ] Check cache hit rates
- [ ] Optimize rate limiting if needed
- [ ] Review SSL/TLS performance
- [ ] Plan for scaling if needed

### Documentation & Handover
- [ ] Document deployment procedures
- [ ] Create runbooks for common tasks
- [ ] Document troubleshooting procedures
- [ ] Train operations team
- [ ] Create disaster recovery procedures
- [ ] Document custom configurations

---

## Phase 9: Security Hardening

### Database Security
- [ ] Verify database user permissions are restrictive
- [ ] Enable SSL connections
- [ ] Set up automated backups with encryption
- [ ] Review database activity logs
- [ ] Set up database firewall rules
- [ ] Disable default accounts

### Application Security
- [ ] Enable security headers in all responses
- [ ] Configure CSRF protection
- [ ] Set up rate limiting
- [ ] Enable API authentication
- [ ] Set up API key rotation
- [ ] Review permission settings

### Infrastructure Security
- [ ] Configure firewall rules
- [ ] Set up DDoS protection (if needed)
- [ ] Enable WAF rules (if needed)
- [ ] Configure VPC/Network security
- [ ] Set up intrusion detection
- [ ] Review access logs

### Compliance & Audit
- [ ] Document security measures
- [ ] Create audit logs
- [ ] Set up log retention
- [ ] Document access control
- [ ] Create security incident procedures
- [ ] Schedule security audits

---

## Phase 10: Backup & Disaster Recovery

### Backup Configuration
- [ ] Set up automated daily backups
- [ ] Verify backup integrity regularly
- [ ] Store backups in secure location
- [ ] Set up backup encryption
- [ ] Test restore procedures
- [ ] Document backup procedures

### Disaster Recovery
- [ ] Create disaster recovery plan
- [ ] Document RTO (Recovery Time Objective)
- [ ] Document RPO (Recovery Point Objective)
- [ ] Test recovery procedures
- [ ] Create failover procedures
- [ ] Document communication procedures

### Maintenance
- [ ] Schedule regular database maintenance
- [ ] Plan index rebuilds
- [ ] Schedule VACUUM operations
- [ ] Monitor disk space
- [ ] Plan capacity expansion
- [ ] Review and update documentation

---

## Ongoing Maintenance

### Weekly Tasks
- [ ] Monitor application logs
- [ ] Check database performance
- [ ] Review error rates
- [ ] Verify backups completed successfully
- [ ] Monitor disk space usage

### Monthly Tasks
- [ ] Review slow query logs
- [ ] Analyze access patterns
- [ ] Update documentation
- [ ] Review security logs
- [ ] Test disaster recovery

### Quarterly Tasks
- [ ] Full security audit
- [ ] Performance optimization review
- [ ] Capacity planning
- [ ] Training updates
- [ ] Backup strategy review

### Annual Tasks
- [ ] Major version updates (Django, PostgreSQL)
- [ ] Full infrastructure review
- [ ] Security penetration testing
- [ ] Complete disaster recovery drill
- [ ] Strategic planning for next year

---

## Quick Reference

### Important Files
```
config/settings/
├── base.py         - Base configuration
├── dev.py          - Development settings
└── prod.py         - Production settings (NEW)

docker-compose-dev.yaml   - Development Docker setup
docker-compose-prod.yaml  - Production Docker setup (NEW)

Dockerfile.dev     - Development Dockerfile
Dockerfile.prod    - Production Dockerfile (NEW)

nginx.conf         - Nginx configuration (NEW)

scripts/
├── backup-database.sh   - Database backup
├── restore-database.sh  - Database restore
├── manage.sh            - Django commands
└── deploy.sh            - Deployment script
```

### Key Commands

```bash
# Development
docker-compose -f docker-compose-dev.yaml up -d
python manage.py migrate
python manage.py createsuperuser

# Production
cp .env.example.prod .env.prod
chmod +x scripts/*.sh
./scripts/deploy.sh
./scripts/manage.sh migrate
./scripts/manage.sh createsuperuser

# Backup
./scripts/backup-database.sh

# Restore
./scripts/restore-database.sh backups/backup_file.sql.gz
```

### Support Documentation
- Full Migration Guide: `POSTGRESQL_MIGRATION_GUIDE.md`
- Implementation Summary: `IMPLEMENTATION_SUMMARY.md`
- Code Review: `CODE_REVIEW.md`
- This Checklist: `DEPLOYMENT_CHECKLIST.md`

---

## Notes & Issues

### Issue #1: [Description]
- Status: [ ] Open [ ] In Progress [ ] Resolved
- Impact: [ ] Low [ ] Medium [ ] High
- Resolution: [Details]

### Issue #2: [Description]
- Status: [ ] Open [ ] In Progress [ ] Resolved
- Impact: [ ] Low [ ] Medium [ ] High
- Resolution: [Details]

---

## Sign-Off

### Developer Sign-Off
- [ ] Code reviewed and tested
- Name: ________________
- Date: ________________
- Signature: ________________

### QA Sign-Off
- [ ] Testing completed successfully
- Name: ________________
- Date: ________________
- Signature: ________________

### Operations Sign-Off
- [ ] Deployment completed successfully
- Name: ________________
- Date: ________________
- Signature: ________________

### Management Approval
- [ ] Approved for production
- Name: ________________
- Date: ________________
- Signature: ________________

---

**Document Status:** Ready for Implementation  
**Last Updated:** November 25, 2025  
**Version:** 1.0
