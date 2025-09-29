# ⚡ Quick Deploy - Canvas MCP Server to AWS EC2

**5-minute deployment from GitHub to AWS EC2**

## 🚀 One-Command Deployment

### Step 1: Upload to GitHub

```bash
# In your local canvas-mcp directory
git init
git add .
git commit -m "Canvas MCP Server - Ready for deployment"
git remote add origin https://github.com/your-username/canvas-mcp.git
git push -u origin main
```

### Step 2: Deploy to AWS EC2

```bash
# SSH to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# One-command deployment
git clone https://github.com/your-username/canvas-mcp.git && \
cd canvas-mcp && \
chmod +x setup.sh && \
./setup.sh
```

### Step 3: Start the Server

```bash
# Choose your deployment model:

# Option A: Multi-tenant (recommended - each user provides their own credentials)
sudo /opt/canvas-mcp/manage.sh start-multi

# Option B: Single-tenant (you provide credentials for all users)
sudo /opt/canvas-mcp/manage.sh start-single
```

## ✅ That's It!

Your Canvas MCP Server is now running! 🎉

### Check Status
```bash
sudo /opt/canvas-mcp/manage.sh status
```

### View Logs
```bash
sudo /opt/canvas-mcp/manage.sh logs
```

### Monitor Server
```bash
sudo /opt/canvas-mcp/monitor.sh
```

## 🔧 Management Commands

```bash
# Start/stop/restart
sudo /opt/canvas-mcp/manage.sh start-multi
sudo /opt/canvas-mcp/manage.sh stop
sudo /opt/canvas-mcp/manage.sh restart

# View logs
sudo /opt/canvas-mcp/manage.sh logs

# Check status
sudo /opt/canvas-mcp/manage.sh status

# Update from GitHub
sudo /opt/canvas-mcp/manage.sh update
```

## 🔐 Security Models

### Multi-Tenant (Recommended)
- ✅ Each user provides their own Canvas credentials
- ✅ Complete data isolation
- ✅ Maximum security
- ✅ No shared credentials

### Single-Tenant
- ⚠️ You provide credentials for all users
- ⚠️ All users see the same data
- ✅ Simpler setup

## 📖 Documentation

- **Full Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Security**: [deploy/SECURITY-MODEL.md](deploy/SECURITY-MODEL.md)
- **Quick Start**: [deploy/QUICK-START.md](deploy/QUICK-START.md)

## 🚨 Troubleshooting

```bash
# Check service status
sudo systemctl status canvas-mcp-multi-tenant

# View recent logs
sudo journalctl -u canvas-mcp-multi-tenant -f

# Check system resources
sudo /opt/canvas-mcp/monitor.sh
```

## 🎯 Next Steps

1. **Test the server**: Use the health check endpoints
2. **Configure monitoring**: Set up CloudWatch (optional)
3. **Update regularly**: Use `sudo /opt/canvas-mcp/manage.sh update`
4. **Monitor logs**: Check for any errors or issues

Your Canvas MCP Server is now ready for production use! 🚀
