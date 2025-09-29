#!/bin/bash

# User data script for Canvas MCP Server EC2 instance
# This script runs when the instance first boots

set -e

# Update system
apt-get update
apt-get upgrade -y

# Install required packages
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    htop \
    unzip \
    jq \
    ufw

# Create application directory
mkdir -p /opt/canvas-mcp
cd /opt/canvas-mcp

# Clone the repository (you'll need to replace this with your actual repo)
# For now, we'll create a placeholder
echo "Canvas MCP Server will be deployed here" > README.txt

# Set up firewall
ufw --force enable
ufw allow ssh
ufw allow 8000/tcp

# Create system user for the application
useradd -r -s /bin/false -d /opt/canvas-mcp canvas-mcp

# Set up log directory
mkdir -p /var/log/canvas-mcp-server
chown canvas-mcp:canvas-mcp /var/log/canvas-mcp-server

# Create a simple health check script
cat > /opt/canvas-mcp/health-check.sh << 'EOF'
#!/bin/bash
# Simple health check for the Canvas MCP Server
if systemctl is-active --quiet canvas-mcp-server; then
    echo "Service is running"
    exit 0
else
    echo "Service is not running"
    exit 1
fi
EOF

chmod +x /opt/canvas-mcp/health-check.sh

# Create a deployment script
cat > /opt/canvas-mcp/deploy.sh << 'EOF'
#!/bin/bash
# Deployment script for Canvas MCP Server

set -e

APP_DIR="/opt/canvas-mcp"
SERVICE_NAME="canvas-mcp-server"

echo "Deploying Canvas MCP Server..."

# Stop service if running
systemctl stop $SERVICE_NAME || true

# Update code (replace with your actual deployment method)
# git pull origin main

# Install/update dependencies
cd $APP_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -e .

# Set permissions
chown -R canvas-mcp:canvas-mcp $APP_DIR

# Start service
systemctl start $SERVICE_NAME
systemctl enable $SERVICE_NAME

echo "Deployment completed!"
EOF

chmod +x /opt/canvas-mcp/deploy.sh

# Create systemd service file
cat > /etc/systemd/system/canvas-mcp-server.service << 'EOF'
[Unit]
Description=Canvas MCP Server
After=network.target

[Service]
Type=simple
User=canvas-mcp
Group=canvas-mcp
WorkingDirectory=/opt/canvas-mcp
Environment=PATH=/opt/canvas-mcp/venv/bin
ExecStart=/opt/canvas-mcp/venv/bin/canvas-mcp-server
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=canvas-mcp-server

[Install]
WantedBy=multi-user.target
EOF

# Create environment file template
cat > /opt/canvas-mcp/.env.template << 'EOF'
# Canvas MCP Server Configuration
# Copy this to .env and fill in your actual values

CANVAS_API_TOKEN=your_canvas_api_token_here
CANVAS_API_URL=https://your-institution.canvas.edu/api/v1
MCP_SERVER_NAME=canvas-api
DEBUG=false
API_TIMEOUT=30
CACHE_TTL=300
ENABLE_DATA_ANONYMIZATION=true
ANONYMIZATION_DEBUG=false
INSTITUTION_NAME=Your Institution Name
EOF

# Set permissions
chown -R canvas-mcp:canvas-mcp /opt/canvas-mcp

# Enable service (but don't start yet - needs configuration)
systemctl daemon-reload
systemctl enable canvas-mcp-server

# Create a setup script for the user
cat > /home/ubuntu/setup-canvas-mcp.sh << 'EOF'
#!/bin/bash
# Setup script for Canvas MCP Server

echo "Setting up Canvas MCP Server..."

# Copy environment template
cp /opt/canvas-mcp/.env.template /opt/canvas-mcp/.env

echo "Please edit /opt/canvas-mcp/.env with your Canvas credentials:"
echo "sudo nano /opt/canvas-mcp/.env"
echo ""
echo "Then start the service:"
echo "sudo systemctl start canvas-mcp-server"
echo "sudo systemctl status canvas-mcp-server"
EOF

chmod +x /home/ubuntu/setup-canvas-mcp.sh

# Log completion
echo "Canvas MCP Server setup completed at $(date)" >> /var/log/canvas-mcp-setup.log
