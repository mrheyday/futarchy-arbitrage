#!/bin/bash
# Setup logrotate for Futarchy Arbitrage Bot
#
# This script installs the logrotate configuration for automatic log management
#
# Usage:
#   chmod +x scripts/setup_logrotate.sh
#   sudo ./scripts/setup_logrotate.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGROTATE_CONF="${PROJECT_DIR}/config/logrotate.conf"
LOGROTATE_DEST="/etc/logrotate.d/futarchy-arbitrage"

echo -e "${GREEN}Futarchy Arbitrage Bot - Logrotate Setup${NC}"
echo "=========================================="
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then
	echo -e "${RED}Error: This script must be run as root (use sudo)${NC}"
	exit 1
fi

# Check if logrotate is installed
if ! command -v logrotate &>/dev/null; then
	echo -e "${YELLOW}Warning: logrotate is not installed${NC}"
	echo "Installing logrotate..."

	if command -v apt-get &>/dev/null; then
		apt-get update && apt-get install -y logrotate
	elif command -v yum &>/dev/null; then
		yum install -y logrotate
	else
		echo -e "${RED}Error: Could not install logrotate automatically${NC}"
		echo "Please install logrotate manually and run this script again"
		exit 1
	fi
fi

# Check if config file exists
if [ ! -f "$LOGROTATE_CONF" ]; then
	echo -e "${RED}Error: Logrotate config file not found at ${LOGROTATE_CONF}${NC}"
	exit 1
fi

# Create temporary config with correct paths
echo "Creating logrotate configuration..."
TEMP_CONF=$(mktemp)
sed "s|/path/to/futarchy-arbitrage-1|${PROJECT_DIR}|g" "$LOGROTATE_CONF" >"$TEMP_CONF"

# Get current user (the one who ran sudo)
ACTUAL_USER="${SUDO_USER:-$USER}"
ACTUAL_GROUP=$(id -gn "$ACTUAL_USER")

# Replace www-data with actual user
sed -i "s/www-data/$ACTUAL_USER/g" "$TEMP_CONF"

# Install the configuration
echo "Installing logrotate configuration to ${LOGROTATE_DEST}..."
cp "$TEMP_CONF" "$LOGROTATE_DEST"
chmod 644 "$LOGROTATE_DEST"
rm "$TEMP_CONF"

# Set correct ownership on logs directory
echo "Setting permissions on logs directory..."
chown -R "$ACTUAL_USER:$ACTUAL_GROUP" "${PROJECT_DIR}/logs"
chmod 755 "${PROJECT_DIR}/logs"

# Test the configuration
echo
echo "Testing logrotate configuration..."
if logrotate -d "$LOGROTATE_DEST" 2>&1 | grep -q "error"; then
	echo -e "${RED}Error: Logrotate configuration test failed${NC}"
	echo "Run 'logrotate -d ${LOGROTATE_DEST}' to see details"
	exit 1
else
	echo -e "${GREEN}✓ Logrotate configuration test passed${NC}"
fi

# Create a cron job for logrotate if it doesn't exist
if ! crontab -l 2>/dev/null | grep -q logrotate; then
	echo
	echo -e "${YELLOW}Note: System logrotate usually runs via cron.daily${NC}"
	echo "If you want to run logrotate hourly instead, add this to crontab:"
	echo "  0 * * * * /usr/sbin/logrotate ${LOGROTATE_DEST}"
fi

echo
echo -e "${GREEN}✓ Logrotate setup complete!${NC}"
echo
echo "Configuration installed at: ${LOGROTATE_DEST}"
echo "Logs directory: ${PROJECT_DIR}/logs"
echo
echo "To manually rotate logs: sudo logrotate -f ${LOGROTATE_DEST}"
echo "To test rotation (dry run): sudo logrotate -d ${LOGROTATE_DEST}"
echo
