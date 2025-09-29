#!/bin/bash
# Multi-Tenant Canvas MCP Server Setup Script
# This script sets up the multi-tenant server with all necessary fixes

set -e

echo "🚀 Setting up Multi-Tenant Canvas MCP Server..."

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ This script should not be run as root. Please run as ec2-user."
   exit 1
fi

# Install required Python packages
echo "📦 Installing Python packages..."
python3.11 -m pip install --user fastmcp httpx boto3 python-dotenv pydantic

# Stop existing service if running
echo "🛑 Stopping existing service..."
sudo systemctl stop canvas-mcp-multi-tenant 2>/dev/null || true

# Copy service file
echo "📋 Installing systemd service..."
sudo cp /home/ec2-user/aistudio/HW3/canvas-mcp/deploy/canvas-mcp-multi-tenant.service /etc/systemd/system/

# Reload systemd
echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "✅ Enabling service..."
sudo systemctl enable canvas-mcp-multi-tenant

# Start service
echo "🚀 Starting service..."
sudo systemctl start canvas-mcp-multi-tenant

# Check status
echo "📊 Checking service status..."
sudo systemctl status canvas-mcp-multi-tenant --no-pager

echo "✅ Setup complete!"
echo "📝 To check logs: sudo journalctl -u canvas-mcp-multi-tenant -f"
echo "🛑 To stop: sudo systemctl stop canvas-mcp-multi-tenant"
echo "🔄 To restart: sudo systemctl restart canvas-mcp-multi-tenant"
