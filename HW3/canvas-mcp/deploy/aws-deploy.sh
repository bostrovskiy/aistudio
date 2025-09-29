#!/bin/bash

# AWS Deployment Script for Canvas MCP Server
# This script sets up the Canvas MCP server on an AWS EC2 instance

set -e

echo "🚀 Starting AWS deployment of Canvas MCP Server..."

# Configuration
APP_NAME="canvas-mcp-server"
APP_USER="canvas-mcp"
APP_DIR="/opt/canvas-mcp"
SERVICE_NAME="canvas-mcp-server"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

# Check if running on Ubuntu/Amazon Linux
if ! command -v apt-get &> /dev/null && ! command -v yum &> /dev/null; then
    error "This script supports Ubuntu/Debian and Amazon Linux only."
fi

log "Updating system packages..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get upgrade -y
    sudo apt-get install -y python3 python3-pip python3-venv git curl wget
elif command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip git curl wget
fi

log "Creating application user..."
sudo useradd -r -s /bin/false -d $APP_DIR $APP_USER || true

log "Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

log "Setting up Python virtual environment..."
sudo -u $APP_USER python3 -m venv $APP_DIR/venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip

log "Installing Canvas MCP Server..."
# Copy the application files
sudo cp -r /home/ubuntu/canvas-mcp/* $APP_DIR/ 2>/dev/null || sudo cp -r ./canvas-mcp/* $APP_DIR/
sudo chown -R $APP_USER:$APP_USER $APP_DIR

# Install dependencies
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -e $APP_DIR

log "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Canvas MCP Server
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/canvas-mcp-server
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

log "Creating environment configuration..."
sudo tee $APP_DIR/.env > /dev/null <<EOF
# Canvas MCP Server Configuration
# Replace these values with your actual Canvas credentials

# Your Canvas API token (get from Canvas → Account → Settings → New Access Token)
CANVAS_API_TOKEN=your_canvas_api_token_here

# Your Canvas API URL (usually your institution's Canvas URL + /api/v1)
CANVAS_API_URL=https://your-institution.canvas.edu/api/v1

# Server configuration
MCP_SERVER_NAME=canvas-api
DEBUG=false
API_TIMEOUT=30
CACHE_TTL=300

# Privacy settings (recommended to keep enabled)
ENABLE_DATA_ANONYMIZATION=true
ANONYMIZATION_DEBUG=false

# Optional: Institution name for display
INSTITUTION_NAME=Your Institution Name
EOF

sudo chown $APP_USER:$APP_USER $APP_DIR/.env
sudo chmod 600 $APP_DIR/.env

log "Setting up log rotation..."
sudo tee /etc/logrotate.d/$SERVICE_NAME > /dev/null <<EOF
/var/log/$SERVICE_NAME/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 $APP_USER $APP_USER
    postrotate
        systemctl reload $SERVICE_NAME
    endscript
}
EOF

log "Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

warn "⚠️  IMPORTANT: Before starting the service, you need to:"
warn "1. Edit $APP_DIR/.env with your actual Canvas credentials"
warn "2. Run: sudo systemctl start $SERVICE_NAME"
warn "3. Check status: sudo systemctl status $SERVICE_NAME"
warn "4. View logs: sudo journalctl -u $SERVICE_NAME -f"

log "✅ Deployment completed successfully!"
log "Next steps:"
log "1. Edit the .env file: sudo nano $APP_DIR/.env"
log "2. Start the service: sudo systemctl start $SERVICE_NAME"
log "3. Check status: sudo systemctl status $SERVICE_NAME"
