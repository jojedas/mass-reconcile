# Docker Commands Reference

Quick reference for common Docker commands when working with this Odoo development environment.

## Container Management

### Start and Stop

```bash
# Start all containers
docker-compose up -d

# Start and show logs
docker-compose up

# Stop all containers
docker-compose down

# Stop and remove volumes (DELETES DATA!)
docker-compose down -v

# Restart all containers
docker-compose restart

# Restart only Odoo
docker-compose restart odoo

# Restart only database
docker-compose restart db
```

### Container Status

```bash
# Show running containers
docker-compose ps

# Show all containers (including stopped)
docker-compose ps -a

# Show resource usage
docker stats

# Show container details
docker-compose logs odoo --tail=50
```

## Logs and Debugging

### View Logs

```bash
# Follow all logs
docker-compose logs -f

# Follow Odoo logs only
docker-compose logs -f odoo

# Follow database logs only
docker-compose logs -f db

# Show last 100 lines
docker-compose logs --tail=100 odoo

# Show logs with timestamps
docker-compose logs -f -t odoo
```

### Shell Access

```bash
# Open bash shell in Odoo container
docker-compose exec odoo bash

# Open bash shell in database container
docker-compose exec db bash

# Run a single command in Odoo container
docker-compose exec odoo ls -la /mnt/custom-addons

# Run a single command in database container
docker-compose exec db psql -U odoo -l
```

## Database Operations

### PostgreSQL Commands

```bash
# Connect to PostgreSQL shell
docker-compose exec db psql -U odoo -d jumo

# List all databases
docker-compose exec db psql -U odoo -l

# List all tables in jumo database
docker-compose exec db psql -U odoo -d jumo -c "\dt"

# Backup database
docker-compose exec -T db pg_dump -U odoo jumo > backup_$(date +%Y%m%d).sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U odoo jumo

# Drop database (CAREFUL!)
docker-compose exec db psql -U odoo -c "DROP DATABASE IF EXISTS jumo;"

# Create database
docker-compose exec db psql -U odoo -c "CREATE DATABASE jumo OWNER odoo;"
```

### Database Queries

```bash
# Check database size
docker-compose exec db psql -U odoo -d jumo -c "
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database
WHERE pg_database.datname = 'jumo';
"

# List installed modules
docker-compose exec db psql -U odoo -d jumo -c "
SELECT name, state, latest_version
FROM ir_module_module
WHERE state = 'installed'
ORDER BY name;
"

# Check Odoo version
docker-compose exec db psql -U odoo -d jumo -c "
SELECT name, value
FROM ir_config_parameter
WHERE key = 'database.uuid';
"
```

## Odoo Module Operations

### Install Modules

```bash
# Install a module
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --init=MODULE_NAME \
    --stop-after-init

# Install multiple modules
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --init=account,account_reconcile_oca \
    --stop-after-init
```

### Update/Upgrade Modules

```bash
# Update a module
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --update=MODULE_NAME \
    --stop-after-init

# Update all modules
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --update=all \
    --stop-after-init

# Update and restart
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --update=mass_reconcile \
    --stop-after-init && \
docker-compose restart odoo
```

### Uninstall Modules

```bash
# Uninstall via shell (safest method)
docker-compose exec odoo odoo shell -d jumo <<EOF
module = env['ir.module.module'].search([('name', '=', 'MODULE_NAME')])
module.button_immediate_uninstall()
EOF
```

## File Operations

### Copy Files

```bash
# Copy file from host to container
docker cp /path/on/host/file.py odoo_app:/mnt/custom-addons/

# Copy file from container to host
docker cp odoo_app:/var/lib/odoo/filestore/jumo/ ./backup/

# Copy entire directory
docker cp ./my_addon/ odoo_app:/mnt/extra-addons/
```

### View Files

```bash
# View Odoo config
docker-compose exec odoo cat /etc/odoo/odoo.conf

# List addons directories
docker-compose exec odoo ls -la /mnt/custom-addons
docker-compose exec odoo ls -la /mnt/oca-addons

# Check Python version
docker-compose exec odoo python3 --version

# Check Odoo version
docker-compose exec odoo odoo --version
```

## Cleanup and Maintenance

### Remove Unused Resources

```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove unused volumes
docker volume prune

# Remove everything (CAREFUL!)
docker system prune -a --volumes
```

### Rebuild Containers

```bash
# Rebuild without cache
docker-compose build --no-cache

# Rebuild and restart
docker-compose up -d --build

# Pull latest images
docker-compose pull
```

## Advanced Operations

### Performance and Monitoring

```bash
# Show real-time resource usage
docker stats odoo_app

# Show container processes
docker-compose top

# Show port mappings
docker-compose port odoo 8069
```

### Network Operations

```bash
# List networks
docker network ls

# Inspect network
docker network inspect mass_reconcile_odoo_network

# Show container IPs
docker-compose exec odoo hostname -i
docker-compose exec db hostname -i
```

### Execute Python Code

```bash
# Run Python code in Odoo context
docker-compose exec odoo odoo shell -d jumo <<EOF
print(env['ir.module.module'].search([('state', '=', 'installed')]).mapped('name'))
EOF

# Interactive Python shell
docker-compose exec odoo python3
```

## Troubleshooting Commands

### Check Container Health

```bash
# Check if containers are healthy
docker-compose ps

# Inspect container
docker inspect odoo_app

# Check container logs for errors
docker-compose logs odoo | grep -i error
docker-compose logs odoo | grep -i exception
```

### Port Conflicts

```bash
# Check what's using port 8069
sudo lsof -i :8069
sudo netstat -tlnp | grep 8069

# Check all ports used by Docker
docker-compose ps --format "{{.Ports}}"
```

### Permission Issues

```bash
# Fix permissions in data directories
sudo chown -R $USER:$USER data/
chmod -R 755 data/

# Check file ownership in container
docker-compose exec odoo ls -la /var/lib/odoo
```

### Reset Environment

```bash
# Complete reset (DELETES EVERYTHING!)
docker-compose down -v
sudo rm -rf data/postgres/* data/odoo/*
docker-compose up -d
```

## Quick Scripts

### Full Reset Script

```bash
#!/bin/bash
# Save as reset.sh and chmod +x reset.sh

echo "Stopping containers..."
docker-compose down -v

echo "Cleaning data..."
rm -rf data/postgres/* data/odoo/*

echo "Restarting containers..."
docker-compose up -d

echo "Waiting for Odoo to start..."
sleep 30

echo "Done! Go to http://localhost:8069 to create database"
```

### Database Backup Script

```bash
#!/bin/bash
# Save as backup.sh and chmod +x backup.sh

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/jumo_${DATE}.sql"

mkdir -p "$BACKUP_DIR"

echo "Backing up database to ${BACKUP_FILE}..."
docker-compose exec -T db pg_dump -U odoo jumo > "$BACKUP_FILE"

echo "Backup complete!"
echo "File: ${BACKUP_FILE}"
echo "Size: $(du -h ${BACKUP_FILE} | cut -f1)"
```

### Update All Modules Script

```bash
#!/bin/bash
# Save as update-all.sh and chmod +x update-all.sh

echo "Updating all modules..."
docker-compose run --rm odoo odoo \
    --database=jumo \
    --db_host=db \
    --db_user=odoo \
    --db_password=jumo \
    --update=all \
    --stop-after-init

echo "Restarting Odoo..."
docker-compose restart odoo

echo "Done! Check logs: docker-compose logs -f odoo"
```

## Environment Variables

You can create a `.env` file for environment-specific settings:

```bash
# .env file
POSTGRES_PASSWORD=jumo
POSTGRES_USER=odoo
ODOO_ADMIN_PASSWORD=jumo
ODOO_DB_NAME=jumo
```

Then use in docker-compose.yml:
```yaml
environment:
  - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
```

## Tips and Best Practices

1. **Always use `-T` flag** with `docker-compose exec` when piping input/output
2. **Use `--rm` flag** with `docker-compose run` to auto-remove containers
3. **Check logs first** when something doesn't work
4. **Backup before major changes** like module upgrades
5. **Use named volumes** for production (already configured)
6. **Don't commit data/** directory to git (already in .gitignore)
7. **Use `make` commands** for common operations (easier to remember)

## References

- [Docker Compose CLI Reference](https://docs.docker.com/compose/reference/)
- [Docker CLI Reference](https://docs.docker.com/engine/reference/commandline/cli/)
- [Odoo Docker Documentation](https://hub.docker.com/_/odoo)
- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)
