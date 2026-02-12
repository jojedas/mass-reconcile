# Documentation Index

Complete guide to the Odoo 18.0 Mass Reconciliation Development Environment.

## Quick Navigation

### Getting Started (Start Here!)

1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
   - Fastest way to set up the environment
   - 3-step setup process
   - Essential commands only

2. **[README.md](README.md)** - Project overview
   - What this project does
   - Technology stack
   - Quick command reference

### Detailed Documentation

3. **[SETUP.md](SETUP.md)** - Complete setup guide
   - Prerequisites
   - Step-by-step installation
   - Configuration details
   - Troubleshooting
   - Development tips

4. **[DOCKER_COMMANDS.md](DOCKER_COMMANDS.md)** - Docker reference
   - All Docker commands you'll need
   - Container management
   - Database operations
   - Module installation via CLI
   - Advanced operations
   - Quick scripts

5. **[TEST_ENVIRONMENT.md](TEST_ENVIRONMENT.md)** - Testing guide
   - How to verify your setup
   - 10 tests to run
   - Common issues and solutions
   - Performance benchmarks

## Files by Category

### Configuration Files

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Docker Compose configuration |
| `config/odoo.conf` | Odoo server configuration |
| `.dockerignore` | Files to exclude from Docker context |
| `.gitignore` | Files to exclude from Git |

### Scripts

| File | Purpose | Usage |
|------|---------|-------|
| `setup.sh` | Initial environment setup | `./setup.sh` |
| `install-modules.sh` | Install required Odoo modules | `./install-modules.sh` |
| `Makefile` | Convenient command shortcuts | `make help` |

### Documentation

| File | Purpose | Audience |
|------|---------|----------|
| `README.md` | Project overview | Everyone |
| `QUICKSTART.md` | Quick start guide | New users |
| `SETUP.md` | Complete setup guide | All users |
| `DOCKER_COMMANDS.md` | Docker command reference | Developers |
| `TEST_ENVIRONMENT.md` | Testing guide | QA/Developers |
| `INDEX.md` | This file | Navigation |

### Module Files

| File | Purpose |
|------|---------|
| `__init__.py` | Module initialization |
| `__manifest__.py` | Module metadata |
| `models/` | Python model definitions |
| `security/` | Access rights and rules |

## Common Tasks

### First Time Setup

1. Read: [QUICKSTART.md](QUICKSTART.md)
2. Run: `./setup.sh`
3. Create database at http://localhost:8069
4. Run: `./install-modules.sh`
5. Test: Follow [TEST_ENVIRONMENT.md](TEST_ENVIRONMENT.md)

### Daily Development

1. Start: `make start` or `docker-compose up -d`
2. Code: Edit your module files
3. Update: `make upgrade-module MODULE=mass_reconcile`
4. Test: Access http://localhost:8069
5. Debug: `make logs-odoo`
6. Stop: `make stop` or `docker-compose down`

### Troubleshooting

1. Check: `make status`
2. Logs: `make logs-odoo`
3. Restart: `make restart-odoo`
4. If stuck: See [SETUP.md](SETUP.md) Troubleshooting section
5. Still stuck: See [DOCKER_COMMANDS.md](DOCKER_COMMANDS.md) for advanced debugging

### Learning Docker Commands

- Basic commands: [QUICKSTART.md](QUICKSTART.md)
- All commands: [DOCKER_COMMANDS.md](DOCKER_COMMANDS.md)
- Quick reference: `make help`

## Directory Structure

```
mass_reconcile/
├── Documentation
│   ├── INDEX.md                    ← You are here
│   ├── README.md                   ← Start here
│   ├── QUICKSTART.md               ← Quick setup
│   ├── SETUP.md                    ← Detailed guide
│   ├── DOCKER_COMMANDS.md          ← Command reference
│   └── TEST_ENVIRONMENT.md         ← Testing guide
│
├── Configuration
│   ├── docker-compose.yml          ← Docker setup
│   ├── config/odoo.conf            ← Odoo config
│   ├── .dockerignore               ← Docker excludes
│   └── .gitignore                  ← Git excludes
│
├── Scripts
│   ├── setup.sh                    ← Initial setup
│   ├── install-modules.sh          ← Module installer
│   └── Makefile                    ← Command shortcuts
│
├── Module Code
│   ├── __init__.py                 ← Module init
│   ├── __manifest__.py             ← Module manifest
│   ├── models/                     ← Python models
│   └── security/                   ← Security rules
│
└── Data (not in Git)
    ├── data/postgres/              ← Database files
    ├── data/odoo/                  ← Odoo filestore
    └── addons/oca/                 ← OCA modules
```

## Quick Reference

### Essential Commands

```bash
# Setup (first time only)
./setup.sh

# Start environment
make start                          # or: docker-compose up -d

# Stop environment
make stop                           # or: docker-compose down

# View logs
make logs-odoo                      # or: docker-compose logs -f odoo

# Restart after code changes
make restart-odoo                   # or: docker-compose restart odoo

# Update module
make upgrade-module MODULE=mass_reconcile

# Access shell
make shell                          # or: docker-compose exec odoo bash

# Database backup
make backup

# See all commands
make help
```

### Important URLs

- Odoo Web: http://localhost:8069
- Database: localhost:5432

### Credentials

- Database Name: `jumo`
- Database User: `odoo`
- Database Password: `jumo`
- Master Password: `jumo`

## FAQ

### Which file should I read first?

Start with [QUICKSTART.md](QUICKSTART.md) if you want to get running quickly, or [README.md](README.md) for an overview.

### Where are the Docker commands?

See [DOCKER_COMMANDS.md](DOCKER_COMMANDS.md) for comprehensive Docker command reference.

### How do I troubleshoot issues?

1. Check [QUICKSTART.md](QUICKSTART.md) Common Commands section
2. See [SETUP.md](SETUP.md) Troubleshooting section
3. Review [TEST_ENVIRONMENT.md](TEST_ENVIRONMENT.md) Common Issues

### Where is the Odoo configuration?

- Docker setup: `docker-compose.yml`
- Odoo settings: `config/odoo.conf`

### How do I add more OCA modules?

Clone them to `addons/oca/` directory, restart Odoo, and install via Apps menu.

### Can I use a different database name?

Yes, but you'll need to update:
- `docker-compose.yml` (command section)
- `config/odoo.conf` (db_name)
- Scripts: `setup.sh`, `install-modules.sh`

### How do I reset everything?

```bash
make clean          # Careful: deletes all data!
./setup.sh          # Start fresh
```

## Support and Resources

### Documentation Order (Recommended)

1. **Quick Start**: [QUICKSTART.md](QUICKSTART.md) → Get running in 5 minutes
2. **Overview**: [README.md](README.md) → Understand the project
3. **Detailed Setup**: [SETUP.md](SETUP.md) → Learn all features
4. **Commands**: [DOCKER_COMMANDS.md](DOCKER_COMMANDS.md) → Master Docker
5. **Testing**: [TEST_ENVIRONMENT.md](TEST_ENVIRONMENT.md) → Verify setup

### External Resources

- [Odoo 18.0 Documentation](https://www.odoo.com/documentation/18.0/)
- [OCA account-reconcile](https://github.com/OCA/account-reconcile)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)

## Contributing

When contributing to this project:

1. Read the documentation
2. Follow Odoo development guidelines
3. Test your changes with [TEST_ENVIRONMENT.md](TEST_ENVIRONMENT.md)
4. Document any new features

## Version Information

- Odoo Version: 18.0 Community
- PostgreSQL Version: 15
- Python Version: 3.11+ (in Docker image)
- Docker Compose Version: 3.8

---

**Last Updated**: 2026-02-12

**Maintained By**: Development Team

**Status**: Active Development
