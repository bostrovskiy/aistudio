# Multi-Tenant Canvas MCP Server Deployment

This guide covers deploying the multi-tenant Canvas MCP server with all necessary fixes.

## 🔧 **Fixed Issues**

The following issues have been resolved in the source code:

1. **Missing `time` import** - Added `import time` to prevent `name 'time' is not defined` error
2. **Asyncio event loop conflicts** - Added proper asyncio handling for systemd services
3. **Python version compatibility** - Configured to use Python 3.11 explicitly
4. **Service configuration** - Proper systemd service file with correct paths and environment variables

## 🚀 **Quick Deployment**

### Option 1: Automated Setup
```bash
# Run the setup script
cd /home/ec2-user/aistudio/HW3/canvas-mcp
./deploy/setup-multi-tenant.sh
```

### Option 2: Manual Setup
```bash
# 1. Install dependencies
python3.11 -m pip install --user fastmcp httpx boto3 python-dotenv pydantic

# 2. Copy service file
sudo cp deploy/canvas-mcp-multi-tenant.service /etc/systemd/system/

# 3. Reload and start
sudo systemctl daemon-reload
sudo systemctl enable canvas-mcp-multi-tenant
sudo systemctl start canvas-mcp-multi-tenant

# 4. Check status
sudo systemctl status canvas-mcp-multi-tenant
```

## 🔍 **Troubleshooting**

### Check Service Status
```bash
sudo systemctl status canvas-mcp-multi-tenant
```

### View Logs
```bash
sudo journalctl -u canvas-mcp-multi-tenant -f
```

### Test Manually
```bash
cd /home/ec2-user/aistudio/HW3/canvas-mcp
PYTHONPATH=/home/ec2-user/.local/lib/python3.11/site-packages python3.11 deploy/multi-tenant-server.py
```

## 🛠 **Service Management**

```bash
# Start service
sudo systemctl start canvas-mcp-multi-tenant

# Stop service
sudo systemctl stop canvas-mcp-multi-tenant

# Restart service
sudo systemctl restart canvas-mcp-multi-tenant

# Check status
sudo systemctl status canvas-mcp-multi-tenant

# View logs
sudo journalctl -u canvas-mcp-multi-tenant -f
```

## 📋 **Service Configuration**

The service file includes:
- **User**: `ec2-user` (not root)
- **Python**: `/usr/bin/python3.11` (explicit version)
- **Working Directory**: `/home/ec2-user/aistudio/HW3/canvas-mcp`
- **Environment**: Proper PATH and PYTHONPATH
- **Restart Policy**: Always restart on failure
- **Logging**: Journal integration

## 🔐 **Security Features**

- **Multi-tenant architecture**: Each user provides their own Canvas credentials
- **Session isolation**: User sessions are completely isolated
- **Automatic cleanup**: Expired sessions are automatically removed
- **No shared credentials**: No risk of credential leakage between users

## ✅ **Success Indicators**

When working correctly, you should see:
- Service status: `Active: active (running)`
- No error messages in logs
- Server starts successfully with authentication prompts
- Users can authenticate with their own Canvas credentials
