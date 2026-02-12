# Quick Start Guide

Get your Odoo 18.0 development environment running in 3 steps!

## Prerequisites

- Docker and Docker Compose installed
- Git installed
- Ports 8069, 5432 available

## Step 1: Setup (First Time Only)

```bash
./setup.sh
```

This will:
- Create necessary directories
- Clone OCA account-reconcile modules
- Start Docker containers
- Wait for Odoo to be ready

**Estimated time**: 3-5 minutes

## Step 2: Create Database

1. Open browser: **http://localhost:8069**

2. Click **"Create Database"**

3. Fill in:
   - Master Password: `jumo`
   - Database Name: `jumo`
   - Email: your@email.com
   - Password: (your choice)
   - Language: English
   - Demo data: **unchecked**

4. Click **"Create Database"**

**Estimated time**: 2-3 minutes

## Step 3: Install Modules

### Option A: Web Interface (Easy)

1. Go to **Apps** menu
2. Remove "Apps" filter (click the × next to it)
3. Install these modules:
   - **Accounting** (`account`)
   - **Account Reconcile OCA** (`account_reconcile_oca`)
   - **Account Reconcile Model OCA** (`account_reconcile_model_oca`)

### Option B: Command Line (Faster)

```bash
./install-modules.sh
```

**Estimated time**: 5-10 minutes

## That's It!

You now have a fully functional Odoo 18.0 development environment with OCA accounting modules.

Access Odoo at: **http://localhost:8069**

## Common Commands

Using Docker Compose:
```bash
docker-compose up -d          # Start
docker-compose down           # Stop
docker-compose logs -f odoo   # View logs
docker-compose restart odoo   # Restart after code changes
```

Using Makefile (easier):
```bash
make start           # Start
make stop            # Stop
make logs-odoo       # View logs
make restart-odoo    # Restart after code changes
make help            # See all commands
```

## Install Your Custom Module

1. Enable developer mode: **Settings** → **Activate developer mode**
2. Go to **Apps** → **Update Apps List**
3. Search for "mass_reconcile"
4. Click **Install**

Or via command line:
```bash
make upgrade-module MODULE=mass_reconcile
```

## Need Help?

- Full documentation: See `SETUP.md`
- Check logs: `make logs-odoo`
- Container status: `make status`
- List all commands: `make help`

## Troubleshooting

**Odoo not accessible?**
```bash
docker-compose ps              # Check if running
docker-compose logs odoo       # Check for errors
docker-compose restart         # Restart
```

**Port already in use?**
```bash
sudo lsof -i :8069            # Check what's using the port
```
Then either stop that service or change the port in `docker-compose.yml`

**Need to start fresh?**
```bash
make clean                    # Removes everything (CAREFUL!)
./setup.sh                    # Start over
```

## Next Steps

- Configure accounting: **Accounting** → **Configuration**
- Create chart of accounts
- Set up journals
- Configure reconciliation models
- Start developing your mass reconciliation features!

Happy coding!
