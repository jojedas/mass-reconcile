# Odoo 18.0 Community Development Environment Setup

This guide will help you set up a complete Odoo 18.0 development environment with OCA accounting modules using Docker.

## Overview

This environment includes:
- **Odoo 18.0 Community Edition** (official Docker image)
- **PostgreSQL 15** database
- **OCA account-reconcile modules** for mass reconciliation
- **Custom addons support** for your own modules

## Prerequisites

- Docker Engine (version 20.10 or later)
- Docker Compose (version 2.0 or later)
- Git
- At least 4GB of free RAM
- At least 10GB of free disk space

## Quick Start

### Option 1: Automated Setup (Recommended)

Run the setup script to automatically configure everything:

```bash
./setup.sh
```

This script will:
1. Create necessary directories
2. Clone OCA account-reconcile modules (18.0 branch)
3. Start Docker containers
4. Wait for Odoo to be ready

After the script completes, go to http://localhost:8069 and create the database.

### Option 2: Manual Setup

If you prefer manual control:

```bash
# 1. Create directories
mkdir -p config data/postgres data/odoo addons/oca addons/extra

# 2. Clone OCA modules
git clone --branch 18.0 --depth 1 https://github.com/OCA/account-reconcile.git addons/oca/account-reconcile

# 3. Set permissions
chmod -R 777 data/

# 4. Start Docker containers
docker-compose up -d

# 5. View logs to monitor startup
docker-compose logs -f odoo
```

## Creating the Database

1. Open your browser and go to: **http://localhost:8069**

2. Click **"Create Database"**

3. Fill in the database details:
   - **Master Password**: `jumo`
   - **Database Name**: `jumo`
   - **Email**: your@email.com
   - **Password**: (choose a secure password for the admin user)
   - **Phone**: (optional)
   - **Language**: English
   - **Country**: (select your country)
   - **Demo data**: Leave **unchecked** (we don't want demo data)

4. Click **"Create Database"**

5. Wait for the database to be created (this may take 1-2 minutes)

## Installing Required Modules

### Method 1: Web Interface (Recommended for beginners)

1. After logging in, go to **Apps** menu

2. Click the **"Filters"** dropdown and remove the **"Apps"** filter (click the × next to it)

3. Search for and install these modules in order:
   - **Accounting** (`account`) - Base accounting module
   - **Account Reconcile OCA** (`account_reconcile_oca`) - OCA reconciliation features
   - **Account Reconcile Model OCA** (`account_reconcile_model_oca`) - Reconciliation models

4. Click **"Install"** on each module and wait for it to complete

### Method 2: Command Line (Automated)

```bash
./install-modules.sh
```

This script will automatically install all required modules.

### Method 3: Manual Command Line

```bash
# Install base accounting
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --init=account \
    --stop-after-init \
    --without-demo=all

# Restart Odoo
docker-compose restart odoo
```

Repeat for other modules: `account_reconcile_oca`, `account_reconcile_model_oca`

## Installing Your Custom Module

Your current project (`mass_reconcile`) is already mounted in the container at `/mnt/custom-addons`.

To install it:

1. Go to **Settings** → **Activate the developer mode**

2. Go to **Apps** → **Update Apps List**

3. Search for your module name and click **Install**

Alternatively, via command line:

```bash
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --init=mass_reconcile \
    --stop-after-init

docker-compose restart odoo
```

## Daily Usage

### Start the Environment

```bash
docker-compose up -d
```

Access Odoo at: http://localhost:8069

### Stop the Environment

```bash
docker-compose down
```

### Restart Odoo (after code changes)

```bash
docker-compose restart odoo
```

### View Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow only Odoo logs
docker-compose logs -f odoo

# Follow only database logs
docker-compose logs -f db
```

### Access Container Shell

```bash
# Access Odoo container
docker-compose exec odoo bash

# Access database container
docker-compose exec db bash

# Run PostgreSQL commands
docker-compose exec db psql -U odoo -d jumo
```

### Update Module After Code Changes

```bash
# Method 1: Web interface
# Go to Apps → Find your module → Upgrade

# Method 2: Command line (faster)
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --update=mass_reconcile \
    --stop-after-init

docker-compose restart odoo
```

## Directory Structure

```
mass_reconcile/
├── docker-compose.yml          # Docker Compose configuration
├── setup.sh                    # Automated setup script
├── install-modules.sh          # Module installation script
├── SETUP.md                    # This file
├── config/
│   └── odoo.conf              # Odoo configuration file
├── data/
│   ├── postgres/              # PostgreSQL data (persistent)
│   └── odoo/                  # Odoo filestore (persistent)
├── addons/
│   ├── oca/                   # OCA modules directory
│   │   └── account-reconcile/ # OCA account-reconcile modules
│   └── extra/                 # Additional third-party modules
├── models/                    # Your custom module models
├── security/                  # Your custom module security
├── __init__.py               # Your custom module init
└── __manifest__.py           # Your custom module manifest
```

## Configuration Details

### Database Credentials

- **Database Host**: `db` (container name)
- **Database Port**: `5432`
- **Database User**: `odoo`
- **Database Password**: `jumo`
- **Database Name**: `jumo`
- **Master Password**: `jumo`

### Ports

- **8069**: Odoo web interface (http://localhost:8069)
- **8071**: XML-RPC port (for external integrations)
- **8072**: Long polling (for live chat and notifications)
- **5432**: PostgreSQL (direct database access)

### Addons Paths

The following directories are mounted as addon paths (in order of priority):

1. `/mnt/custom-addons` → Your current project directory
2. `/mnt/oca-addons` → OCA modules
3. `/mnt/extra-addons` → Additional third-party modules
4. `/usr/lib/python3/dist-packages/odoo/addons` → Standard Odoo modules

## Available OCA Modules

After running the setup, the following OCA modules should be available:

- `account_reconcile_oca` - Advanced reconciliation features
- `account_reconcile_model_oca` - Reconciliation models and rules
- `account_mass_reconcile` - Mass reconciliation tool (if available in 18.0)
- And other modules from the account-reconcile repository

## Troubleshooting

### Issue: Odoo is not accessible

**Solution**:
```bash
# Check if containers are running
docker-compose ps

# Check logs for errors
docker-compose logs odoo

# Restart containers
docker-compose restart
```

### Issue: Database connection errors

**Solution**:
```bash
# Check if database is running
docker-compose ps db

# Verify database exists
docker-compose exec db psql -U odoo -l

# Restart database
docker-compose restart db
```

### Issue: Module not found

**Solution**:
```bash
# Update the apps list in Odoo
# Go to Apps → Update Apps List (in debug mode)

# Or via command line
docker-compose restart odoo
```

### Issue: Permission denied errors

**Solution**:
```bash
# Fix permissions
chmod -R 777 data/

# Restart Odoo
docker-compose restart odoo
```

### Issue: Port already in use

**Solution**:
```bash
# Check what's using port 8069
sudo lsof -i :8069

# Either stop that service or change the port in docker-compose.yml
# Change "8069:8069" to "8070:8069" to use port 8070 instead
```

### Issue: Need to start fresh

**Solution**:
```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Remove data directories
rm -rf data/postgres/* data/odoo/*

# Run setup again
./setup.sh
```

## Development Tips

### Enable Developer Mode

1. Go to **Settings**
2. Scroll down to **Developer Tools**
3. Click **Activate the developer mode**

This enables:
- Module installation/upgrade from UI
- Technical menu
- View inheritance debugging
- And many other developer features

### Live Code Reload

The Odoo configuration includes `dev_mode = reload`, which automatically reloads Python code when files change. However, you still need to restart for some changes:

```bash
docker-compose restart odoo
```

### Database Management

```bash
# Backup database
docker-compose exec db pg_dump -U odoo jumo > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U odoo jumo

# Drop database (careful!)
docker-compose exec db psql -U odoo -c "DROP DATABASE jumo;"

# Create database
docker-compose exec db psql -U odoo -c "CREATE DATABASE jumo;"
```

### Performance Tuning

For development, the current settings should be sufficient. For production, consider:

- Increasing workers in `config/odoo.conf`
- Adjusting memory limits
- Using a reverse proxy (nginx)
- Enabling Odoo caching

## Additional Resources

- [Odoo Official Documentation](https://www.odoo.com/documentation/18.0/)
- [OCA Documentation](https://odoo-community.org/)
- [OCA account-reconcile on GitHub](https://github.com/OCA/account-reconcile)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## Support

For issues specific to:
- **Odoo**: Check official Odoo documentation or forums
- **OCA Modules**: Check the GitHub repository issues
- **Docker**: Check Docker documentation or Docker forums
- **This Setup**: Review this guide and check logs

## Next Steps

1. Start the environment: `./setup.sh`
2. Create the database at http://localhost:8069
3. Install required modules
4. Start developing your mass reconciliation features!

Happy coding!
