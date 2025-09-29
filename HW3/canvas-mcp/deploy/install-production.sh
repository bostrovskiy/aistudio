#!/bin/bash

# Canvas MCP Server - Production Installation Script
# This script installs the Canvas MCP server with enterprise-grade security

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error "Please run as root (use sudo)"
    exit 1
fi

log "🚀 Starting Canvas MCP Server Production Installation..."

# Get domain name from user
read -p "Enter your domain name (e.g., yourdomain.com): " DOMAIN
if [ -z "$DOMAIN" ]; then
    error "Domain name is required"
    exit 1
fi

# Get email for SSL certificate
read -p "Enter your email address for SSL certificate: " EMAIL
if [ -z "$EMAIL" ]; then
    error "Email address is required"
    exit 1
fi

log "🌐 Domain: $DOMAIN"
log "📧 Email: $EMAIL"

# Update system
log "📦 Updating system packages..."
yum update -y

# Install Python 3.11
log "🐍 Installing Python 3.11..."
yum install -y python3.11 python3.11-pip python3.11-devel

# Install system dependencies
log "📦 Installing system dependencies..."
yum install -y nginx certbot python3-certbot-nginx curl wget git

# Create application directory
APP_DIR="/opt/canvas-mcp"
log "📁 Creating application directory: $APP_DIR"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone repository (replace with your repository URL)
log "📥 Cloning repository..."
if [ ! -d "canvas-mcp" ]; then
    git clone https://github.com/your-username/canvas-mcp.git
fi

cd canvas-mcp

# Install Python dependencies
log "🐍 Installing Python dependencies..."
pip3.11 install -r deploy/requirements-production.txt

# Create log directory
log "📝 Setting up logging..."
mkdir -p /var/log
touch /var/log/canvas-mcp-security.log
chown ec2-user:ec2-user /var/log/canvas-mcp-security.log

# Create systemd service
log "⚙️ Creating systemd service..."
cat > /etc/systemd/system/canvas-mcp.service << EOF
[Unit]
Description=Canvas MCP Server (Production)
After=network.target

[Service]
Type=simple
User=ec2-user
Group=ec2-user
WorkingDirectory=$APP_DIR/canvas-mcp
Environment=HOST=0.0.0.0
Environment=PORT=8080
Environment=SECURITY_LOG_FILE=/var/log/canvas-mcp-security.log
Environment=MAX_SESSIONS_PER_USER=5
Environment=MAX_REQUESTS_PER_MINUTE=60
Environment=MAX_REQUESTS_PER_IP_PER_MINUTE=100
Environment=CORS_ORIGINS=https://$DOMAIN
ExecStart=/usr/bin/python3.11 $APP_DIR/canvas-mcp/deploy/mcp-http-server-production.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=canvas-mcp

[Install]
WantedBy=multi-user.target
EOF

# Configure nginx
log "🌐 Configuring nginx..."
cat > /etc/nginx/conf.d/canvas-mcp.conf << EOF
upstream canvas_mcp {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL configuration with Let's Encrypt certificates
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL security settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # CORS headers
    add_header Access-Control-Allow-Origin "https://$DOMAIN" always;
    add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
    
    # Proxy to Canvas MCP server
    location / {
        proxy_pass http://canvas_mcp;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}
EOF

# Test nginx configuration
log "🧪 Testing nginx configuration..."
nginx -t

# Get SSL certificate
log "🔒 Obtaining SSL certificate..."
certbot certonly --standalone -d $DOMAIN --non-interactive --agree-tos --email $EMAIL

# Start services
log "🚀 Starting services..."
systemctl daemon-reload
systemctl enable canvas-mcp
systemctl start canvas-mcp
systemctl enable nginx
systemctl start nginx

# Set up automatic certificate renewal
log "🔄 Setting up automatic certificate renewal..."
(crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -

# Set up log rotation
log "📝 Setting up log rotation..."
cat > /etc/logrotate.d/canvas-mcp << EOF
/var/log/canvas-mcp-security.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 ec2-user ec2-user
}
EOF

# Test installation
log "🧪 Testing installation..."
sleep 5
curl -I https://$DOMAIN/ || warn "SSL test failed - check firewall and security groups"

# Show status
log "📊 Service status:"
systemctl status canvas-mcp --no-pager
systemctl status nginx --no-pager

log "✅ Installation complete!"
log "🌐 Your secure endpoint: https://$DOMAIN/"
log "🔒 SSL certificate will auto-renew"
log "📋 Logs: /var/log/canvas-mcp-security.log"
log "⚙️ Service: systemctl status canvas-mcp"

warn "⚠️  IMPORTANT: Configure your firewall to allow ports 80 and 443"
warn "⚠️  IMPORTANT: Update your DNS to point $DOMAIN to this server"
