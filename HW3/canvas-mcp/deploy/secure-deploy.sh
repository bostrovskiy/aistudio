#!/bin/bash

# Secure deployment script for Canvas MCP Server on AWS
# This script uses AWS Secrets Manager for credential storage

set -e

# Configuration
APP_NAME="canvas-mcp-server"
APP_USER="canvas-mcp"
APP_DIR="/opt/canvas-mcp"
SERVICE_NAME="canvas-mcp-server"
SECRET_NAME="canvas-mcp-credentials"
AWS_REGION="us-east-1"

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

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    log "Installing AWS CLI..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    log "Installing Python 3..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Install boto3 for AWS integration
log "Installing AWS SDK..."
pip3 install boto3

# Create application user
log "Creating application user..."
sudo useradd -r -s /bin/false -d $APP_DIR $APP_USER || true

# Create application directory
log "Creating application directory..."
sudo mkdir -p $APP_DIR
sudo chown $APP_USER:$APP_USER $APP_DIR

# Copy application files
log "Installing application..."
sudo cp -r . $APP_DIR/
sudo chown -R $APP_USER:$APP_USER $APP_DIR

# Install Python dependencies
log "Installing Python dependencies..."
sudo -u $APP_USER python3 -m venv $APP_DIR/venv
sudo -u $APP_USER $APP_DIR/venv/bin/pip install --upgrade pip
sudo -u $APP_USER $APP_DIR/venv/bin/pip install -e $APP_DIR
sudo -u $APP_USER $APP_DIR/venv/bin/pip install boto3

# Create secure environment loader
log "Creating secure environment loader..."
sudo tee $APP_DIR/load-secrets.py > /dev/null <<EOF
#!/usr/bin/env python3
"""
Secure environment loader for Canvas MCP Server
Loads credentials from AWS Secrets Manager
"""

import boto3
import json
import os
import sys

def load_canvas_credentials():
    """Load Canvas credentials from AWS Secrets Manager."""
    try:
        # Initialize Secrets Manager client
        client = boto3.client('secretsmanager', region_name='${AWS_REGION}')
        
        # Retrieve the secret
        response = client.get_secret_value(SecretId='${SECRET_NAME}')
        credentials = json.loads(response['SecretString'])
        
        # Set environment variables
        os.environ['CANVAS_API_TOKEN'] = credentials['api_token']
        os.environ['CANVAS_API_URL'] = credentials['api_url']
        
        if 'institution_name' in credentials:
            os.environ['INSTITUTION_NAME'] = credentials['institution_name']
        
        print("✅ Loaded credentials from AWS Secrets Manager", file=sys.stderr)
        return True
        
    except Exception as e:
        print(f"❌ Error loading credentials: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    load_canvas_credentials()
EOF

sudo chmod +x $APP_DIR/load-secrets.py
sudo chown $APP_USER:$APP_USER $APP_DIR/load-secrets.py

# Create systemd service with secure credential loading
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
Environment=PYTHONPATH=$APP_DIR
ExecStartPre=$APP_DIR/venv/bin/python $APP_DIR/load-secrets.py
ExecStart=$APP_DIR/venv/bin/canvas-mcp-server
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
EOF

# Create IAM policy for the service
log "Creating IAM policy..."
sudo tee /tmp/canvas-mcp-policy.json > /dev/null <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": "arn:aws:secretsmanager:${AWS_REGION}:*:secret:${SECRET_NAME}*"
        }
    ]
}
EOF

# Create setup script for credentials
log "Creating credential setup script..."
sudo tee $APP_DIR/setup-credentials.sh > /dev/null <<EOF
#!/bin/bash
# Setup script for Canvas MCP Server credentials

echo "🔐 Canvas MCP Server Credential Setup"
echo "======================================"
echo ""

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI not configured. Please run: aws configure"
    exit 1
fi

echo "📋 Current AWS identity:"
aws sts get-caller-identity

echo ""
echo "Please enter your Canvas credentials:"
echo ""

read -p "Canvas API Token: " -s API_TOKEN
echo ""
read -p "Canvas API URL (e.g., https://your-school.canvas.edu/api/v1): " API_URL
read -p "Institution Name (optional): " INSTITUTION_NAME

echo ""
echo "Storing credentials in AWS Secrets Manager..."

# Use the Python script to store credentials
python3 << PYTHON_SCRIPT
import boto3
import json

try:
    client = boto3.client('secretsmanager', region_name='${AWS_REGION}')
    
    secret_value = {
        "api_token": "$API_TOKEN",
        "api_url": "$API_URL",
        "institution_name": "$INSTITUTION_NAME"
    }
    
    # Try to update existing secret
    try:
        client.update_secret(
            SecretId='${SECRET_NAME}',
            SecretString=json.dumps(secret_value)
        )
        print("✅ Updated existing secret")
    except client.exceptions.ResourceNotFoundException:
        # Create new secret
        client.create_secret(
            Name='${SECRET_NAME}',
            Description='Canvas MCP Server API credentials',
            SecretString=json.dumps(secret_value)
        )
        print("✅ Created new secret")
    
    print("✅ Credentials stored successfully!")
    
except Exception as e:
    print(f"❌ Error storing credentials: {e}")
    exit(1)
PYTHON_SCRIPT

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Credentials stored successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Start the service: sudo systemctl start $SERVICE_NAME"
    echo "2. Check status: sudo systemctl status $SERVICE_NAME"
    echo "3. View logs: sudo journalctl -u $SERVICE_NAME -f"
else
    echo "❌ Failed to store credentials"
    exit 1
fi
EOF

sudo chmod +x $APP_DIR/setup-credentials.sh
sudo chown $APP_USER:$APP_USER $APP_DIR/setup-credentials.sh

# Create credential management script
log "Creating credential management script..."
sudo tee $APP_DIR/manage-credentials.sh > /dev/null <<EOF
#!/bin/bash
# Credential management script for Canvas MCP Server

case "\$1" in
    "setup")
        $APP_DIR/setup-credentials.sh
        ;;
    "test")
        echo "Testing credential retrieval..."
        python3 $APP_DIR/load-secrets.py
        if [ \$? -eq 0 ]; then
            echo "✅ Credentials loaded successfully"
        else
            echo "❌ Failed to load credentials"
        fi
        ;;
    "update")
        $APP_DIR/setup-credentials.sh
        ;;
    "delete")
        echo "Deleting credentials from AWS Secrets Manager..."
        aws secretsmanager delete-secret --secret-id ${SECRET_NAME} --force-delete-without-recovery
        ;;
    *)
        echo "Usage: \$0 {setup|test|update|delete}"
        echo ""
        echo "Commands:"
        echo "  setup   - Set up credentials for the first time"
        echo "  test    - Test credential retrieval"
        echo "  update  - Update existing credentials"
        echo "  delete  - Delete credentials from AWS"
        exit 1
        ;;
esac
EOF

sudo chmod +x $APP_DIR/manage-credentials.sh
sudo chown $APP_USER:$APP_USER $APP_DIR/manage-credentials.sh

# Enable service
log "Enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Create log directory
sudo mkdir -p /var/log/$SERVICE_NAME
sudo chown $APP_USER:$APP_USER /var/log/$SERVICE_NAME

log "✅ Secure deployment completed successfully!"
echo ""
info "🔐 Security Features Enabled:"
info "  - Credentials stored in AWS Secrets Manager"
info "  - No plaintext credentials on disk"
info "  - IAM-based access control"
info "  - Encrypted credential storage"
echo ""
warn "⚠️  Next Steps:"
warn "1. Configure AWS credentials: aws configure"
warn "2. Set up Canvas credentials: sudo $APP_DIR/manage-credentials.sh setup"
warn "3. Start the service: sudo systemctl start $SERVICE_NAME"
warn "4. Check status: sudo systemctl status $SERVICE_NAME"
echo ""
info "📋 Management Commands:"
info "  Setup credentials: sudo $APP_DIR/manage-credentials.sh setup"
info "  Test credentials:   sudo $APP_DIR/manage-credentials.sh test"
info "  Update credentials: sudo $APP_DIR/manage-credentials.sh update"
info "  Delete credentials: sudo $APP_DIR/manage-credentials.sh delete"
