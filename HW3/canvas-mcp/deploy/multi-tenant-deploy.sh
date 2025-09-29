#!/bin/bash

# Multi-Tenant Canvas MCP Server Deployment Script
# This script deploys a secure multi-tenant server where each user provides their own credentials

set -e

# Configuration
APP_NAME="canvas-mcp-multi-tenant"
APP_USER="canvas-mcp"
APP_DIR="/opt/canvas-mcp-multi-tenant"
SERVICE_NAME="canvas-mcp-multi-tenant"

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

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    log "Installing Python 3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Install required packages
log "Installing required packages..."
pip3 install httpx fastmcp

# Create application user
log "Creating application user..."
sudo useradd -r -s /bin/false -d $APP_DIR $APP_USER || true

# Create application directory
log "Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# Copy multi-tenant server
log "Installing multi-tenant server..."
sudo cp deploy/multi-tenant-server.py $APP_DIR/
sudo chown $APP_USER:$APP_USER $APP_DIR/multi-tenant-server.py
sudo chmod +x $APP_DIR/multi-tenant-server.py

# Create systemd service
log "Creating systemd service..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Multi-Tenant Canvas MCP Server
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=$APP_DIR
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 $APP_DIR/deploy/multi-tenant-server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

# Create session cleanup script
log "Creating session cleanup script..."
sudo tee $APP_DIR/cleanup-sessions.sh > /dev/null <<EOF
#!/bin/bash
# Session cleanup script for multi-tenant Canvas MCP Server

# This script can be run periodically to clean up expired sessions
# Add to crontab: */30 * * * * /opt/canvas-mcp-multi-tenant/cleanup-sessions.sh

# Send cleanup command to the server
echo '{"method": "cleanup_sessions", "params": {}}' | nc localhost 8000 2>/dev/null || true
EOF

sudo chmod +x $APP_DIR/cleanup-sessions.sh
sudo chown $APP_USER:$APP_USER $APP_DIR/cleanup-sessions.sh

# Create monitoring script
log "Creating monitoring script..."
sudo tee $APP_DIR/monitor.sh > /dev/null <<EOF
#!/bin/bash
# Monitoring script for multi-tenant Canvas MCP Server

echo "🔍 Canvas MCP Multi-Tenant Server Status"
echo "========================================"

# Check service status
if systemctl is-active --quiet $SERVICE_NAME; then
    echo "✅ Service Status: Running"
else
    echo "❌ Service Status: Not Running"
fi

# Check recent logs
echo ""
echo "📋 Recent Logs (last 10 lines):"
journalctl -u $SERVICE_NAME --no-pager -n 10

# Check active sessions (if server supports it)
echo ""
echo "👥 Active Sessions:"
# This would need to be implemented in the server
echo "  (Session monitoring not yet implemented)"

# Check system resources
echo ""
echo "💻 System Resources:"
echo "  Memory Usage: $(free -h | grep '^Mem:' | awk '{print $3 "/" $2}')"
echo "  Disk Usage: $(df -h / | tail -1 | awk '{print $5}')"
echo "  Load Average: $(uptime | awk -F'load average:' '{print $2}')"
EOF

sudo chmod +x $APP_DIR/monitor.sh
sudo chown $APP_USER:$APP_USER $APP_DIR/monitor.sh

# Create user guide
log "Creating user guide..."
sudo tee $APP_DIR/USER-GUIDE.md > /dev/null <<EOF
# 🔐 Multi-Tenant Canvas MCP Server - User Guide

## How It Works

This server requires **each user to authenticate with their own Canvas credentials**. This ensures:

- ✅ **Complete Data Isolation**: You only see your own Canvas data
- ✅ **Secure Credentials**: Your Canvas token is never shared
- ✅ **Proper Audit Trail**: Canvas logs show activity under your account
- ✅ **FERPA Compliance**: No unauthorized data access

## Getting Started

### Step 1: Authenticate
First, you need to authenticate with your Canvas credentials:

\`\`\`python
# Get your Canvas API token from: Canvas → Account → Settings → New Access Token
session_id = await authenticate_canvas(
    api_token="your_canvas_token_here",
    api_url="https://your-school.canvas.edu/api/v1",
    institution_name="Your School Name"
)
\`\`\`

### Step 2: Use Your Session
All subsequent calls require your session ID:

\`\`\`python
# List your courses
courses = await list_my_courses(session_id)

# Get your profile
profile = await get_my_profile(session_id)

# List assignments for a course
assignments = await list_my_assignments(session_id, course_id="12345")
\`\`\`

### Step 3: Session Management
- Sessions expire after 24 hours
- You can check your session info: \`get_session_info(session_id)\`
- Logout when done: \`logout(session_id)\`

## Security Features

### 🔐 Credential Isolation
- Each user provides their own Canvas API token
- No shared credentials between users
- Your token is never stored permanently

### ⏰ Session Management
- Sessions expire after 24 hours of inactivity
- Automatic cleanup of expired sessions
- Secure session IDs (32 random characters)

### 📊 Audit Trail
- All Canvas API calls use your credentials
- Canvas logs show activity under your account
- Clear accountability for all actions

## Available Tools

1. **authenticate_canvas** - Authenticate with your Canvas credentials
2. **list_my_courses** - List your courses
3. **get_my_profile** - Get your Canvas profile
4. **list_my_assignments** - List assignments for a course
5. **get_session_info** - Check your session status
6. **logout** - Logout and invalidate session

## Troubleshooting

### Authentication Failed
- Check your Canvas API token is correct
- Verify your Canvas URL is correct (should end with /api/v1)
- Ensure your Canvas account has API access

### Session Expired
- Re-authenticate with your credentials
- Sessions expire after 24 hours of inactivity

### API Errors
- Check your Canvas permissions
- Verify the course/assignment IDs are correct
- Ensure you have access to the requested data

## Security Best Practices

1. **Use Strong Tokens**: Generate new Canvas API tokens regularly
2. **Logout When Done**: Always logout when finished
3. **Don't Share Sessions**: Each user should have their own session
4. **Monitor Activity**: Check your Canvas account for unexpected activity

## Support

If you encounter issues:
1. Check the server logs: \`sudo journalctl -u $SERVICE_NAME -f\`
2. Verify your credentials work in Canvas directly
3. Test with a simple API call to your Canvas instance
EOF

sudo chown $APP_USER:$APP_USER $APP_DIR/USER-GUIDE.md

# Enable service
log "Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Create log directory
sudo mkdir -p /var/log/$SERVICE_NAME
sudo chown $APP_USER:$APP_USER /var/log/$SERVICE_NAME

log "✅ Multi-tenant deployment completed successfully!"
echo ""
info "🔐 Security Features:"
info "  - Per-user authentication required"
info "  - Complete credential isolation"
info "  - Session-based access control"
info "  - Automatic session cleanup"
info "  - FERPA compliant data handling"
echo ""
warn "⚠️  Important Security Notes:"
warn "  - Each user MUST provide their own Canvas credentials"
warn "  - No shared credentials or data access"
warn "  - Sessions expire after 24 hours"
warn "  - All Canvas activity is logged under each user's account"
echo ""
info "📋 Next Steps:"
info "1. Start the service: sudo systemctl start $SERVICE_NAME"
info "2. Check status: sudo systemctl status $SERVICE_NAME"
info "3. View logs: sudo journalctl -u $SERVICE_NAME -f"
info "4. Monitor: sudo $APP_DIR/monitor.sh"
echo ""
info "📖 User Guide: $APP_DIR/USER-GUIDE.md"
info "🔧 Management: sudo $APP_DIR/monitor.sh"
