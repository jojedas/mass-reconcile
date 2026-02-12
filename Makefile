# Makefile for Odoo 18.0 Development Environment
# Provides convenient shortcuts for common Docker Compose commands

.PHONY: help setup start stop restart logs logs-odoo logs-db shell shell-db status clean backup restore install-modules upgrade-module psql

# Default target
help:
	@echo "Odoo 18.0 Development Environment - Available Commands:"
	@echo ""
	@echo "  make setup              - Initial setup (clone OCA modules, start containers)"
	@echo "  make start              - Start all containers"
	@echo "  make stop               - Stop all containers"
	@echo "  make restart            - Restart all containers"
	@echo "  make restart-odoo       - Restart only Odoo container"
	@echo "  make logs               - Show logs from all containers (follow)"
	@echo "  make logs-odoo          - Show logs from Odoo only (follow)"
	@echo "  make logs-db            - Show logs from database only (follow)"
	@echo "  make shell              - Open bash shell in Odoo container"
	@echo "  make shell-db           - Open bash shell in database container"
	@echo "  make psql               - Open PostgreSQL shell for jumo database"
	@echo "  make status             - Show container status"
	@echo "  make clean              - Stop containers and remove volumes (DESTRUCTIVE)"
	@echo "  make install-modules    - Install required Odoo modules"
	@echo "  make upgrade-module     - Upgrade a specific module (usage: make upgrade-module MODULE=mass_reconcile)"
	@echo "  make update-apps-list   - Update Odoo apps list"
	@echo "  make backup             - Backup jumo database to backup.sql"
	@echo "  make restore            - Restore jumo database from backup.sql"
	@echo ""

# Initial setup
setup:
	@echo "Running initial setup..."
	@./setup.sh

# Start containers
start:
	@echo "Starting containers..."
	@docker-compose up -d
	@echo "Odoo is starting up... Access at http://localhost:8069"

# Stop containers
stop:
	@echo "Stopping containers..."
	@docker-compose down

# Restart all containers
restart:
	@echo "Restarting containers..."
	@docker-compose restart
	@echo "Containers restarted"

# Restart only Odoo
restart-odoo:
	@echo "Restarting Odoo..."
	@docker-compose restart odoo
	@echo "Odoo restarted"

# Show logs
logs:
	@docker-compose logs -f

# Show Odoo logs
logs-odoo:
	@docker-compose logs -f odoo

# Show database logs
logs-db:
	@docker-compose logs -f db

# Open shell in Odoo container
shell:
	@docker-compose exec odoo bash

# Open shell in database container
shell-db:
	@docker-compose exec db bash

# Open PostgreSQL shell
psql:
	@docker-compose exec db psql -U odoo -d jumo

# Show container status
status:
	@docker-compose ps

# Clean everything (DESTRUCTIVE)
clean:
	@echo "WARNING: This will remove all containers and data!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		rm -rf data/postgres/* data/odoo/*; \
		echo "Cleanup complete"; \
	else \
		echo "Cleanup cancelled"; \
	fi

# Install required modules
install-modules:
	@./install-modules.sh

# Upgrade a specific module
upgrade-module:
	@if [ -z "$(MODULE)" ]; then \
		echo "Error: MODULE parameter is required"; \
		echo "Usage: make upgrade-module MODULE=mass_reconcile"; \
		exit 1; \
	fi
	@echo "Upgrading module: $(MODULE)"
	@docker-compose run --rm odoo odoo \
		--database=jumo \
		--db_host=db \
		--db_user=odoo \
		--db_password=jumo \
		--update=$(MODULE) \
		--stop-after-init
	@docker-compose restart odoo
	@echo "Module $(MODULE) upgraded"

# Update apps list
update-apps-list:
	@echo "Updating apps list..."
	@docker-compose run --rm odoo odoo \
		--database=jumo \
		--db_host=db \
		--db_user=odoo \
		--db_password=jumo \
		--update=base \
		--stop-after-init
	@docker-compose restart odoo
	@echo "Apps list updated"

# Backup database
backup:
	@echo "Backing up jumo database..."
	@docker-compose exec -T db pg_dump -U odoo jumo > backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "Backup created: backup_$(shell date +%Y%m%d_%H%M%S).sql"

# Restore database
restore:
	@if [ ! -f "backup.sql" ]; then \
		echo "Error: backup.sql not found"; \
		echo "Usage: Place your backup file as 'backup.sql' and run 'make restore'"; \
		exit 1; \
	fi
	@echo "Restoring jumo database from backup.sql..."
	@cat backup.sql | docker-compose exec -T db psql -U odoo jumo
	@echo "Database restored"
	@docker-compose restart odoo
