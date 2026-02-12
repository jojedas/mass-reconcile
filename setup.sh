#!/bin/bash
# Odoo 18.0 Development Environment Setup Script
# This script sets up the Docker environment and clones OCA modules

set -e  # Exit on any error

echo "=========================================="
echo "Odoo 18.0 Development Environment Setup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Step 1: Creating necessary directories...${NC}"
mkdir -p config data/postgres data/odoo addons/oca addons/extra

echo -e "${GREEN}✓ Directories created${NC}"
echo ""

echo -e "${BLUE}Step 2: Cloning OCA account-reconcile repository (18.0 branch)...${NC}"
if [ -d "addons/oca/account-reconcile" ]; then
    echo -e "${YELLOW}⚠ account-reconcile directory already exists. Updating...${NC}"
    cd addons/oca/account-reconcile
    git pull origin 18.0
    cd "$SCRIPT_DIR"
else
    git clone --branch 18.0 --depth 1 https://github.com/OCA/account-reconcile.git addons/oca/account-reconcile
fi

echo -e "${GREEN}✓ OCA account-reconcile modules cloned${NC}"
echo ""

echo -e "${BLUE}Step 3: Checking OCA modules available...${NC}"
if [ -d "addons/oca/account-reconcile" ]; then
    echo "Available OCA modules:"
    ls -1 addons/oca/account-reconcile/ | grep -v "^setup" | grep -v "^\.git" | grep -v "^README" | grep -v "LICENSE"
fi
echo ""

echo -e "${BLUE}Step 4: Setting proper permissions...${NC}"
# Ensure Odoo can write to data directories
chmod -R 777 data/
echo -e "${GREEN}✓ Permissions set${NC}"
echo ""

echo -e "${BLUE}Step 5: Starting Docker containers...${NC}"
docker-compose down -v 2>/dev/null || true
docker-compose up -d

echo ""
echo -e "${GREEN}✓ Docker containers started${NC}"
echo ""

echo "=========================================="
echo "Waiting for Odoo to be ready..."
echo "=========================================="
echo ""

# Wait for Odoo to be ready
echo "This may take a minute or two..."
sleep 10

# Check if Odoo is responding
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8069/web/database/selector >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Odoo is ready!${NC}"
        break
    fi
    attempt=$((attempt + 1))
    echo "Waiting... ($attempt/$max_attempts)"
    sleep 5
done

if [ $attempt -eq $max_attempts ]; then
    echo -e "${YELLOW}⚠ Odoo might still be starting up. Check logs with: docker-compose logs -f odoo${NC}"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "1. Access Odoo at: ${BLUE}http://localhost:8069${NC}"
echo ""
echo "2. Create the 'jumo' database:"
echo "   - Click 'Create Database'"
echo "   - Database Name: ${BLUE}jumo${NC}"
echo "   - Master Password: ${BLUE}jumo${NC}"
echo "   - Email: your@email.com"
echo "   - Password: (choose a password)"
echo "   - Language: English"
echo "   - Country: (choose your country)"
echo "   - Demo data: Leave unchecked"
echo ""
echo "3. Install required modules:"
echo "   - Go to Apps menu"
echo "   - Remove 'Apps' filter to see all modules"
echo "   - Install: ${BLUE}Accounting (account)${NC}"
echo "   - Install: ${BLUE}Account Reconcile OCA (account_reconcile_oca)${NC}"
echo "   - Install: ${BLUE}Account Reconcile Model OCA (account_reconcile_model_oca)${NC}"
echo ""
echo "4. Useful commands:"
echo "   - View logs: ${BLUE}docker-compose logs -f odoo${NC}"
echo "   - Stop environment: ${BLUE}docker-compose down${NC}"
echo "   - Restart: ${BLUE}docker-compose restart odoo${NC}"
echo "   - Shell access: ${BLUE}docker-compose exec odoo bash${NC}"
echo ""
echo "=========================================="
