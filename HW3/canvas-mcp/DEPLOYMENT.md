# 🚀 Canvas MCP Server - Deployment Guide

This guide explains how to deploy the Canvas MCP Server to AWS EC2 from GitHub.

## 📋 Prerequisites

- AWS EC2 instance (Ubuntu 20.04+ or Amazon Linux 2+)
- SSH access to your EC2 instance
- Your Canvas API credentials (for single-tenant deployment)

## 🔧 Quick Deployment

### Step 1: Prepare Your GitHub Repository

1. **Upload to GitHub**:
   ```bash
   # Initialize git repository
   git init
   git add .
   git commit -m "Initial commit: Canvas MCP Server"
   
   # Create GitHub repository and push
   git remote add origin https://github.com/your-username/canvas-mcp.git
   git push -u origin main
   ```

2. **Make sure these files are included**:
   - `setup.sh` - Main setup script
   - `deploy/multi-tenant-server.py` - Multi-tenant server
   - `deploy/multi-tenant-deploy.sh` - Multi-tenant deployment
   - `deploy/secure-deploy.sh` - Single-tenant deployment
   - `requirements.txt` - Python dependencies
   - `README.md` - Documentation

### Step 2: Deploy to AWS EC2

1. **SSH to your EC2 instance**:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/canvas-mcp.git
   cd canvas-mcp
   ```

3. **Run the setup script**:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

### Step 3: Choose Your Deployment Model

#### Option A: Multi-Tenant Server (Recommended)

**Best for**: Multiple users, maximum security

```bash
# Start multi-tenant server
sudo /opt/canvas-mcp/manage.sh start-multi

# Check status
sudo /opt/canvas-mcp/manage.sh status

# View logs
sudo /opt/canvas-mcp/manage.sh logs
```

**How it works**:
- Each user authenticates with their own Canvas credentials
- Complete data isolation between users
- No shared credentials or data access

#### Option B: Single-Tenant Server

**Best for**: Personal use only

```bash
# Configure credentials
sudo cp /opt/canvas-mcp/.env.template /opt/canvas-mcp/.env
sudo nano /opt/canvas-mcp/.env

# Start single-tenant server
sudo /opt/canvas-mcp/manage.sh start-single

# Check status
sudo /opt/canvas-mcp/manage.sh status
```

**How it works**:
- You provide Canvas credentials for all users
- All users see the same Canvas data
- Less secure but simpler setup

## 🔧 Management Commands

### Service Management

```bash
# Start servers
sudo /opt/canvas-mcp/manage.sh start-multi    # Multi-tenant
sudo /opt/canvas-mcp/manage.sh start-single   # Single-tenant

# Stop all servers
sudo /opt/canvas-mcp/manage.sh stop

# Restart servers
sudo /opt/canvas-mcp/manage.sh restart

# Check status
sudo /opt/canvas-mcp/manage.sh status

# View logs
sudo /opt/canvas-mcp/manage.sh logs           # Multi-tenant
sudo /opt/canvas-mcp/manage.sh logs-single    # Single-tenant
```

### Monitoring

```bash
# Check server health
sudo /opt/canvas-mcp/monitor.sh

# View system resources
htop
df -h
free -h
```

### Updates

```bash
# Update from GitHub
sudo /opt/canvas-mcp/manage.sh update

# Manual update
cd /opt/canvas-mcp
git pull origin main
sudo systemctl restart canvas-mcp-multi-tenant
```

## 🔐 Security Configuration

### Multi-Tenant Security

- ✅ **No configuration needed** - users provide their own credentials
- ✅ **Complete data isolation** - each user sees only their data
- ✅ **Secure sessions** - 24-hour timeout with automatic cleanup
- ✅ **Audit trail** - all activity logged under user's account

### Single-Tenant Security

1. **Configure credentials**:
   ```bash
   sudo nano /opt/canvas-mcp/.env
   ```

2. **Set secure permissions**:
   ```bash
   sudo chmod 600 /opt/canvas-mcp/.env
   sudo chown canvas-mcp:canvas-mcp /opt/canvas-mcp/.env
   ```

3. **Use AWS Secrets Manager** (optional):
   ```bash
   # Store credentials in AWS Secrets Manager
   aws secretsmanager create-secret \
       --name "canvas-mcp-credentials" \
       --secret-string '{"api_token":"your-token","api_url":"https://..."}'
   ```

## 📊 Monitoring and Logging

### Log Locations

- **System logs**: `/var/log/syslog`
- **Service logs**: `journalctl -u canvas-mcp-multi-tenant`
- **Application logs**: `/var/log/canvas-mcp/`

### Health Checks

```bash
# Check service health
sudo systemctl is-active canvas-mcp-multi-tenant
sudo systemctl is-active canvas-mcp-server

# Test API connectivity
curl -f http://localhost:8000/health || echo "Health check failed"
```

### CloudWatch Integration

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure monitoring
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**:
   ```bash
   sudo journalctl -u canvas-mcp-multi-tenant -f
   sudo systemctl status canvas-mcp-multi-tenant
   ```

2. **Permission denied**:
   ```bash
   sudo chown -R canvas-mcp:canvas-mcp /opt/canvas-mcp
   sudo chmod +x /opt/canvas-mcp/manage.sh
   ```

3. **Authentication failed** (multi-tenant):
   - Check Canvas API token
   - Verify Canvas URL format
   - Ensure API access is enabled

4. **Configuration errors** (single-tenant):
   ```bash
   sudo nano /opt/canvas-mcp/.env
   sudo systemctl restart canvas-mcp-server
   ```

### Debug Commands

```bash
# Full system status
sudo /opt/canvas-mcp/manage.sh status
sudo /opt/canvas-mcp/monitor.sh

# View all logs
sudo journalctl -u canvas-mcp-multi-tenant --since "1 hour ago"
sudo journalctl -u canvas-mcp-server --since "1 hour ago"

# Test connectivity
curl -v http://localhost:8000/
```

## 🔄 Maintenance

### Regular Tasks

1. **Monitor server health**:
   ```bash
   sudo /opt/canvas-mcp/monitor.sh
   ```

2. **Clean up logs**:
   ```bash
   sudo journalctl --vacuum-time=7d
   ```

3. **Update system packages**:
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

4. **Backup configuration**:
   ```bash
   sudo tar -czf canvas-mcp-backup-$(date +%Y%m%d).tar.gz /opt/canvas-mcp/.env
   ```

### Automated Maintenance

Create a cron job for regular maintenance:

```bash
# Edit crontab
sudo crontab -e

# Add maintenance tasks
# Clean up logs weekly
0 2 * * 0 journalctl --vacuum-time=7d

# Update packages weekly
0 3 * * 0 apt-get update && apt-get upgrade -y

# Restart services monthly
0 4 1 * * systemctl restart canvas-mcp-multi-tenant
```

## 📞 Support

### Getting Help

1. **Check logs first**: `sudo /opt/canvas-mcp/manage.sh logs`
2. **Verify service status**: `sudo /opt/canvas-mcp/manage.sh status`
3. **Test connectivity**: Use the health check endpoints
4. **Review documentation**: `/opt/canvas-mcp/README.md`

### Useful Commands

```bash
# Quick health check
sudo /opt/canvas-mcp/monitor.sh

# View recent errors
sudo journalctl -u canvas-mcp-multi-tenant --since "1 hour ago" | grep -i error

# Check disk space
df -h

# Check memory usage
free -h

# Check network connectivity
ping -c 3 google.com
```

## ✅ Success Checklist

- [ ] EC2 instance launched and accessible
- [ ] Repository cloned from GitHub
- [ ] Setup script completed successfully
- [ ] Service running and healthy
- [ ] Logs showing no errors
- [ ] Health checks passing
- [ ] Monitoring configured (optional)

## 🎉 You're Done!

Your Canvas MCP Server is now running on AWS EC2 with:

- ✅ **Secure deployment** with proper user isolation
- ✅ **Easy management** with automated scripts
- ✅ **Comprehensive monitoring** and logging
- ✅ **Simple updates** from GitHub
- ✅ **Production-ready** configuration

The server is ready to handle Canvas API requests with full security and privacy protection! 🚀
