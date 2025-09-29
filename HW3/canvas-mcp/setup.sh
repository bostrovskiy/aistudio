#!/bin/bash

# Canvas MCP Server - Automated Setup Script
# This script sets up the Canvas MCP Server on an AWS EC2 instance

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root. Please run as a regular user with sudo privileges."
fi

# Check if running on Ubuntu/Amazon Linux
if ! command -v apt-get &> /dev/null && ! command -v yum &> /dev/null; then
    error "This script supports Ubuntu/Debian and Amazon Linux only."
fi

echo "🚀 Canvas MCP Server Setup"
echo "=========================="
echo ""

# Update system packages
log "Updating system packages..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update
    sudo apt-get upgrade -y
    sudo apt-get install -y python3 python3-pip python3-venv git curl wget htop unzip jq
elif command -v yum &> /dev/null; then
    sudo yum update -y
    sudo yum install -y python3 python3-pip git curl wget htop unzip jq
fi

# Install Python dependencies
log "Installing Python dependencies..."
pip3 install --upgrade pip
pip3 install httpx fastmcp boto3

# Create application user
log "Creating application user..."
sudo useradd -r -s /bin/false -d /opt/canvas-mcp canvas-mcp || true

# Create application directory
log "Creating application directory..."
sudo mkdir -p /opt/canvas-mcp
sudo chown -R canvas-mcp:canvas-mcp /opt/canvas-mcp

# Copy application files
log "Installing application..."
sudo cp -r . /opt/canvas-mcp/
sudo cp -r ./deploy /opt/canvas-mcp/
sudo cp -r ./src /opt/canvas-mcp/
sudo chown -R canvas-mcp:canvas-mcp /opt/canvas-mcp

# Install the application
log "Installing Canvas MCP Server..."
sudo -u canvas-mcp python3 -m venv /opt/canvas-mcp/venv
sudo -u canvas-mcp /opt/canvas-mcp/venv/bin/pip install --upgrade pip
sudo -u canvas-mcp /opt/canvas-mcp/venv/bin/pip install -e /opt/canvas-mcp
sudo -u canvas-mcp /opt/canvas-mcp/venv/bin/pip install httpx fastmcp boto3

# Create systemd service for multi-tenant server
log "Creating systemd service..."
sudo tee /etc/systemd/system/canvas-mcp-multi-tenant.service > /dev/null <<EOF
[Unit]
Description=Multi-Tenant Canvas MCP Server
After=network.target

[Service]
Type=simple
User=canvas-mcp
Group=canvas-mcp
WorkingDirectory=/opt/canvas-mcp
Environment=PATH=/opt/canvas-mcp/venv/bin
ExecStart=/opt/canvas-mcp/venv/bin/python /opt/canvas-mcp/deploy/multi-tenant-server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=canvas-mcp-multi-tenant

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for single-tenant server
sudo tee /etc/systemd/system/canvas-mcp-server.service > /dev/null <<EOF
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

# Create management scripts
log "Creating management scripts..."

# Service management script
sudo tee /opt/canvas-mcp/manage.sh > /dev/null <<EOF
#!/bin/bash
# Canvas MCP Server Management Script

case "\$1" in
    "start-multi")
        sudo systemctl start canvas-mcp-multi-tenant
        sudo systemctl enable canvas-mcp-multi-tenant
        echo "✅ Multi-tenant server started"
        ;;
    "start-single")
        sudo systemctl start canvas-mcp-server
        sudo systemctl enable canvas-mcp-server
        echo "✅ Single-tenant server started"
        ;;
    "stop")
        sudo systemctl stop canvas-mcp-multi-tenant canvas-mcp-server
        echo "✅ All servers stopped"
        ;;
    "status")
        echo "Multi-tenant server:"
        sudo systemctl status canvas-mcp-multi-tenant --no-pager
        echo ""
        echo "Single-tenant server:"
        sudo systemctl status canvas-mcp-server --no-pager
        ;;
    "logs")
        echo "Multi-tenant server logs:"
        sudo journalctl -u canvas-mcp-multi-tenant -f
        ;;
    "logs-single")
        echo "Single-tenant server logs:"
        sudo journalctl -u canvas-mcp-server -f
        ;;
    "restart")
        sudo systemctl restart canvas-mcp-multi-tenant canvas-mcp-server
        echo "✅ All servers restarted"
        ;;
    "update")
        cd /opt/canvas-mcp
        git pull origin main
        sudo systemctl restart canvas-mcp-multi-tenant canvas-mcp-server
        echo "✅ Server updated and restarted"
        ;;
    *)
        echo "Usage: \$0 {start-multi|start-single|stop|status|logs|logs-single|restart|update}"
        echo ""
        echo "Commands:"
        echo "  start-multi   - Start multi-tenant server (recommended)"
        echo "  start-single  - Start single-tenant server"
        echo "  stop          - Stop all servers"
        echo "  status      - Show server status"
        echo "  logs          - View multi-tenant server logs"
        echo "  logs-single   - View single-tenant server logs"
        echo "  restart       - Restart all servers"
        echo "  update        - Update and restart servers"
        exit 1
        ;;
esac
EOF

sudo chmod +x /opt/canvas-mcp/manage.sh
sudo chown canvas-mcp:canvas-mcp /opt/canvas-mcp/manage.sh

# Create monitoring script
sudo tee /opt/canvas-mcp/monitor.sh > /dev/null <<EOF
#!/bin/bash
# Canvas MCP Server Monitoring Script

echo "🔍 Canvas MCP Server Status"
echo "=========================="

# Check multi-tenant server
if systemctl is-active --quiet canvas-mcp-multi-tenant; then
    echo "✅ Multi-tenant Server: Running"
else
    echo "❌ Multi-tenant Server: Not Running"
fi

# Check single-tenant server
if systemctl is-active --quiet canvas-mcp-server; then
    echo "✅ Single-tenant Server: Running"
else
    echo "❌ Single-tenant Server: Not Running"
fi

echo ""
echo "📋 Recent Logs (last 5 lines):"
echo "Multi-tenant server:"
journalctl -u canvas-mcp-multi-tenant --no-pager -n 5

echo ""
echo "Single-tenant server:"
journalctl -u canvas-mcp-server --no-pager -n 5

echo ""
echo "💻 System Resources:"
echo "  Memory Usage: \$(free -h | grep '^Mem:' | awk '{print \$3 "/" \$2}')"
echo "  Disk Usage: \$(df -h / | tail -1 | awk '{print \$5}')"
echo "  Load Average: \$(uptime | awk -F'load average:' '{print \$2}')"
EOF

sudo chmod +x /opt/canvas-mcp/monitor.sh
sudo chown canvas-mcp:canvas-mcp /opt/canvas-mcp/monitor.sh

# Create log directory
sudo mkdir -p /var/log/canvas-mcp
sudo chown canvas-mcp:canvas-mcp /var/log/canvas-mcp

# Enable services
log "Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable canvas-mcp-multi-tenant
sudo systemctl enable canvas-mcp-server

# Create environment template
log "Creating environment template..."
sudo tee /opt/canvas-mcp/.env.template > /dev/null <<EOF
# Canvas MCP Server Configuration
# Copy this to .env and fill in your actual values

# For single-tenant server only
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

sudo chown canvas-mcp:canvas-mcp /opt/canvas-mcp/.env.template

# Create setup completion message
log "✅ Setup completed successfully!"
echo ""
info "🎯 Next Steps:"
info "1. Choose your deployment model:"
info "   - Multi-tenant (recommended): sudo /opt/canvas-mcp/manage.sh start-multi"
info "   - Single-tenant: sudo /opt/canvas-mcp/manage.sh start-single"
echo ""
info "2. For single-tenant server, configure credentials:"
info "   sudo cp /opt/canvas-mcp/.env.template /opt/canvas-mcp/.env"
info "   sudo nano /opt/canvas-mcp/.env"
echo ""
info "3. Check status:"
info "   sudo /opt/canvas-mcp/manage.sh status"
echo ""
info "4. View logs:"
info "   sudo /opt/canvas-mcp/manage.sh logs"
echo ""
info "5. Monitor server:"
info "   sudo /opt/canvas-mcp/monitor.sh"
echo ""
warn "⚠️  Security Notes:"
warn "  - Multi-tenant: Each user provides their own Canvas credentials"
warn "  - Single-tenant: You provide credentials for all users (less secure)"
warn "  - Multi-tenant is recommended for better security and privacy"
echo ""
info "📖 Documentation: /opt/canvas-mcp/README.md"
info "🔧 Management: sudo /opt/canvas-mcp/manage.sh"
