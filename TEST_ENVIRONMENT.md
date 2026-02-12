# Testing Your Odoo Environment

This guide helps you verify that your Docker-based Odoo development environment is working correctly.

## Pre-flight Checklist

Before starting, verify you have:

- [ ] Docker installed: `docker --version`
- [ ] Docker Compose installed: `docker-compose --version`
- [ ] Git installed: `git --version`
- [ ] Ports 8069, 5432 available: `sudo lsof -i :8069,5432`
- [ ] At least 4GB free RAM: `free -h`
- [ ] At least 10GB free disk space: `df -h .`

## Step-by-Step Testing

### Test 1: Run Setup Script

```bash
./setup.sh
```

**Expected output:**
- Directories created
- OCA repository cloned
- Docker containers started
- "Odoo is ready!" message

**What to check:**
```bash
# Containers should be running
docker-compose ps

# Should see:
# - odoo_app (running)
# - odoo_db (running, healthy)
```

### Test 2: Access Odoo Web Interface

1. Open browser: http://localhost:8069

**Expected:**
- Odoo database creation page loads
- No errors in browser console

**If it doesn't load:**
```bash
# Check Odoo logs
docker-compose logs odoo | tail -50

# Check if port is accessible
curl -I http://localhost:8069
```

### Test 3: Create Database

1. Fill in database creation form:
   - Master password: `jumo`
   - Database name: `jumo`
   - Email: test@test.com
   - Password: test123

2. Click "Create Database"

**Expected:**
- Database creation starts
- Progress indicator shows
- After 1-2 minutes, you're logged into Odoo
- You see the Odoo main screen with Apps menu

**If it fails:**
```bash
# Check database exists
docker-compose exec db psql -U odoo -l | grep jumo

# Check logs
docker-compose logs -f odoo
```

### Test 4: Verify OCA Modules Available

1. Go to **Apps** menu
2. Remove "Apps" filter (click × next to it)
3. Search for "reconcile"

**Expected:**
- You should see modules like:
  - Account Reconcile OCA
  - Account Reconcile Model OCA

**If modules not found:**
```bash
# Check OCA directory exists
ls -la addons/oca/account-reconcile/

# Update apps list
make update-apps-list

# Or manually restart
docker-compose restart odoo
```

### Test 5: Install Accounting Module

1. In Apps, search for "accounting"
2. Click "Install" on "Accounting" module
3. Wait for installation

**Expected:**
- Module installs successfully
- Accounting menu appears in top menu bar

**If installation fails:**
```bash
# Check logs during installation
docker-compose logs -f odoo

# Try command line installation
make install-modules
```

### Test 6: Install OCA Modules

Option A: Web interface
1. Search for "account_reconcile_oca"
2. Click Install

Option B: Script
```bash
./install-modules.sh
```

**Expected:**
- Modules install successfully
- No error messages

### Test 7: Verify Your Custom Module

1. Enable developer mode: **Settings** → **Activate developer mode**
2. Go to **Apps** → **Update Apps List**
3. Search for "mass_reconcile"

**Expected:**
- Your module appears in the list
- Can be installed

**Install your module:**
```bash
make upgrade-module MODULE=mass_reconcile
```

### Test 8: Test Code Changes

1. Make a change to your module (e.g., edit `__manifest__.py`)
2. Upgrade module:
```bash
make upgrade-module MODULE=mass_reconcile
```

**Expected:**
- Changes are reflected in Odoo
- No errors during upgrade

### Test 9: Database Operations

Test database backup:
```bash
make backup
```

**Expected:**
- Creates backup_YYYYMMDD_HHMMSS.sql file
- No errors

Test PostgreSQL access:
```bash
make psql
```

**Expected:**
- Opens PostgreSQL shell
- Can run SQL: `SELECT * FROM ir_module_module LIMIT 5;`
- Exit with `\q`

### Test 10: Container Management

Test restart:
```bash
make restart-odoo
```

**Expected:**
- Odoo restarts
- Still accessible at http://localhost:8069
- Data persists

Test logs:
```bash
make logs-odoo
```

**Expected:**
- Shows Odoo logs
- Can follow with Ctrl+C to exit

## Common Issues and Solutions

### Issue: Port 8069 already in use

```bash
# Find what's using the port
sudo lsof -i :8069

# Either stop that service, or change port in docker-compose.yml
# Change "8069:8069" to "8070:8069"
```

### Issue: Containers won't start

```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs
docker-compose logs

# Try rebuilding
docker-compose down
docker-compose up -d --build
```

### Issue: "Permission denied" errors

```bash
# Fix data directory permissions
chmod -R 777 data/

# Restart
docker-compose restart
```

### Issue: Database connection errors

```bash
# Check database is healthy
docker-compose ps db

# Should show "healthy" status
# If not, check db logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Issue: Modules not appearing

```bash
# Verify OCA modules are cloned
ls -la addons/oca/account-reconcile/

# If empty, run setup again
./setup.sh

# Update apps list in Odoo
make update-apps-list
```

### Issue: Slow performance

```bash
# Check resource usage
docker stats

# If high, adjust workers in config/odoo.conf
# Change workers = 2 to workers = 0 (for development)

# Restart
docker-compose restart odoo
```

## Verification Checklist

After all tests, you should have:

- [ ] Containers running (odoo_app, odoo_db)
- [ ] Odoo accessible at http://localhost:8069
- [ ] Database "jumo" created
- [ ] Accounting module installed
- [ ] OCA reconcile modules installed
- [ ] Your custom module visible and installable
- [ ] Can restart containers without losing data
- [ ] Can backup/restore database
- [ ] Can view logs
- [ ] Can upgrade modules

## Performance Benchmarks

Your setup should achieve:

- Container startup: < 30 seconds
- Database creation: 1-2 minutes
- Module installation: 30-60 seconds per module
- Page load time: < 2 seconds
- Odoo restart: < 10 seconds

## Next Steps

Once all tests pass:

1. Start developing your mass reconciliation features
2. Test regularly with `make upgrade-module MODULE=mass_reconcile`
3. Keep backups with `make backup`
4. Monitor logs with `make logs-odoo`

## Getting Help

If tests fail:

1. Check the specific error message
2. Look at logs: `make logs-odoo`
3. Review SETUP.md for detailed documentation
4. Check DOCKER_COMMANDS.md for command reference
5. Try `make clean` and start fresh with `./setup.sh`

## Advanced Testing

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test Odoo response time
ab -n 100 -c 10 http://localhost:8069/
```

### Memory Usage

```bash
# Check container memory
docker stats --no-stream odoo_app

# Should be under 1GB for development
```

### Database Size

```bash
docker-compose exec db psql -U odoo -d jumo -c "
SELECT pg_size_pretty(pg_database_size('jumo'));
"
```

### Module Loading Time

```bash
# Time module upgrade
time make upgrade-module MODULE=mass_reconcile
```

---

**Happy Testing!**

If all tests pass, your environment is ready for development.
