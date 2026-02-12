#!/bin/bash
# Script to install Odoo modules via command line
# This requires the database to be already created

set -e

echo "=========================================="
echo "Odoo Module Installation Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

DB_NAME="jumo"
ADMIN_PASSWORD="jumo"

echo -e "${BLUE}This script will install modules in the Odoo database${NC}"
echo -e "Database: ${GREEN}${DB_NAME}${NC}"
echo ""

# Check if database exists
echo -e "${BLUE}Checking if database exists...${NC}"
DB_EXISTS=$(docker-compose exec -T db psql -U odoo -lqt | cut -d \| -f 1 | grep -qw ${DB_NAME} && echo "yes" || echo "no")

if [ "$DB_EXISTS" = "no" ]; then
    echo -e "${RED}✗ Database '${DB_NAME}' does not exist!${NC}"
    echo ""
    echo "Please create the database first:"
    echo "1. Go to http://localhost:8069"
    echo "2. Click 'Create Database'"
    echo "3. Use database name: ${DB_NAME}"
    echo "4. Use master password: ${ADMIN_PASSWORD}"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Database exists${NC}"
echo ""

# Modules to install
MODULES=(
    "account"                           # Base Accounting module
    "account_reconcile_oca"             # OCA Account Reconcile
    "account_reconcile_model_oca"       # OCA Account Reconcile Model
)

echo -e "${BLUE}Modules to install:${NC}"
for module in "${MODULES[@]}"; do
    echo "  - $module"
done
echo ""

echo -e "${YELLOW}Note: This will restart the Odoo container with module installation${NC}"
echo ""

# Install modules
for module in "${MODULES[@]}"; do
    echo -e "${BLUE}Installing module: ${module}${NC}"

    docker-compose run --rm odoo \
        odoo \
        --database=${DB_NAME} \
        --db_host=db \
        --db_user=odoo \
        --db_password=${ADMIN_PASSWORD} \
        --init=${module} \
        --stop-after-init \
        --without-demo=all

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Module ${module} installed successfully${NC}"
    else
        echo -e "${RED}✗ Failed to install module ${module}${NC}"
    fi
    echo ""
done

echo "=========================================="
echo -e "${GREEN}Module installation complete!${NC}"
echo "=========================================="
echo ""
echo "Restarting Odoo..."
docker-compose restart odoo

echo ""
echo -e "${GREEN}Done! Access Odoo at: ${BLUE}http://localhost:8069${NC}"
echo ""
