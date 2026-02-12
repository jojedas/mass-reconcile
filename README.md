# Mass Reconciliation Module for Odoo 18.0

An advanced mass reconciliation module for Odoo 18.0 Community Edition, built on top of OCA's account-reconcile framework.

## Overview

This module provides enhanced mass reconciliation capabilities for Odoo's accounting system, allowing you to efficiently reconcile large volumes of transactions using intelligent matching algorithms and reconciliation models.

## Features

- Mass reconciliation of bank statements and invoices
- Advanced matching algorithms
- Customizable reconciliation rules
- Integration with OCA account-reconcile modules
- Support for complex reconciliation scenarios

## Docker Development Environment

This project includes a complete Docker-based development environment for Odoo 18.0 with all necessary dependencies pre-configured.

### Quick Start

**Get started in 3 steps:**

```bash
# 1. Run automated setup
./setup.sh

# 2. Open browser and create database
# Go to http://localhost:8069
# Database name: jumo
# Master password: jumo

# 3. Install modules
./install-modules.sh
```

See [QUICKSTART.md](QUICKSTART.md) for detailed quick start guide.

### Full Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
- **[SETUP.md](SETUP.md)** - Complete setup and usage documentation

### Command Reference

#### Using Scripts

```bash
./setup.sh                  # Initial setup
./install-modules.sh        # Install required modules
```

#### Using Makefile

```bash
make help                   # Show all available commands
make start                  # Start containers
make stop                   # Stop containers
make restart-odoo           # Restart Odoo
make logs-odoo              # View Odoo logs
make shell                  # Open shell in container
make upgrade-module MODULE=mass_reconcile  # Upgrade module
```

#### Using Docker Compose Directly

```bash
docker-compose up -d        # Start
docker-compose down         # Stop
docker-compose logs -f odoo # View logs
docker-compose restart odoo # Restart
```

## Project Structure

```
mass_reconcile/
├── README.md                    # This file
├── QUICKSTART.md               # Quick start guide
├── SETUP.md                    # Detailed setup guide
├── docker-compose.yml          # Docker Compose configuration
├── Makefile                    # Command shortcuts
├── setup.sh                    # Automated setup script
├── install-modules.sh          # Module installation script
├── config/
│   └── odoo.conf              # Odoo configuration
├── data/                      # Persistent data (not in git)
│   ├── postgres/              # Database files
│   └── odoo/                  # Odoo filestore
├── addons/                    # Third-party addons (not in git)
│   ├── oca/                   # OCA modules
│   └── extra/                 # Additional modules
├── models/                    # Module models
├── security/                  # Module security rules
├── __init__.py               # Module initialization
└── __manifest__.py           # Module manifest
```

## Technology Stack

- **Odoo**: 18.0 Community Edition
- **PostgreSQL**: 15
- **Python**: 3.11 (included in Odoo Docker image)
- **Docker**: For containerization
- **OCA Modules**: account-reconcile framework

## Dependencies

### OCA Modules

- `account_reconcile_oca` - Advanced reconciliation features
- `account_reconcile_model_oca` - Reconciliation models

### Standard Odoo Modules

- `account` - Base accounting module
- `base` - Odoo base module

## Development

### Module Structure

This module follows standard Odoo module structure:

- `models/` - Python model definitions
- `views/` - XML view definitions
- `security/` - Access rights and record rules
- `data/` - Data files (CSV, XML)
- `static/` - Static assets (JS, CSS, images)

### Updating the Module

After making code changes:

```bash
# Method 1: Using Makefile
make upgrade-module MODULE=mass_reconcile

# Method 2: Using Docker Compose
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --update=mass_reconcile \
    --stop-after-init

docker-compose restart odoo
```

### Debugging

Enable developer mode in Odoo:
1. Go to **Settings**
2. Click **Activate the developer mode**

View logs:
```bash
make logs-odoo
```

Access Python shell:
```bash
make shell
python3 -c "import odoo; print(odoo.__version__)"
```

## Configuration

### Database Credentials

- **Database**: jumo
- **User**: odoo
- **Password**: jumo
- **Master Password**: jumo

### Ports

- **8069**: Odoo web interface
- **8071**: XML-RPC
- **8072**: Long polling
- **5432**: PostgreSQL

## Testing

(To be implemented)

```bash
# Run tests
docker-compose run --rm odoo odoo \
    --database=jumo \
    --test-enable \
    --stop-after-init \
    --update=mass_reconcile
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

(Specify your license here - typically AGPL-3 for Odoo modules)

## Authors

- Your Name <your.email@example.com>

## Support

For issues and questions:
- Check the documentation in `SETUP.md`
- Review logs: `make logs-odoo`
- Check container status: `make status`

## Resources

- [Odoo 18.0 Documentation](https://www.odoo.com/documentation/18.0/)
- [OCA account-reconcile](https://github.com/OCA/account-reconcile)
- [Odoo Development Tutorials](https://www.odoo.com/documentation/18.0/developer.html)

## Changelog

### Version 1.0.0 (Initial Release)

- Initial module structure
- Docker development environment setup
- OCA integration
- Basic reconciliation models

---

**Status**: Development

**Odoo Version**: 18.0

**Python Version**: 3.11+

**License**: AGPL-3 (or your chosen license)
