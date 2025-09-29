# Canvas MCP Server

A secure, multi-tenant Message Control Protocol (MCP) server for Canvas Learning Management System integration. This server enables AI-powered interactions with Canvas while maintaining complete data privacy and security.

## 🔐 Security Features

- **Multi-Tenant Architecture**: Each user provides their own Canvas credentials
- **Complete Data Isolation**: Users only see their own Canvas data
- **FERPA Compliant**: Automatic student data anonymization
- **Session Management**: Secure, time-limited sessions
- **Audit Trail**: Clear accountability for all actions

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Canvas API access
- AWS EC2 instance (for deployment)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/canvas-mcp.git
cd canvas-mcp
```

### 2. Deploy to AWS EC2

```bash
# SSH to your EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Clone the repository
git clone https://github.com/your-username/canvas-mcp.git
cd canvas-mcp

# Deploy the multi-tenant server
chmod +x deploy/multi-tenant-deploy.sh
./deploy/multi-tenant-deploy.sh
```

### 3. Start the Service

```bash
# Start the service
sudo systemctl start canvas-mcp-multi-tenant

# Check status
sudo systemctl status canvas-mcp-multi-tenant

# View logs
sudo journalctl -u canvas-mcp-multi-tenant -f
```

## 📁 Project Structure

```
canvas-mcp/
├── src/                          # Source code
│   └── canvas_mcp/
│       ├── core/                 # Core functionality
│       ├── tools/                # MCP tools
│       └── resources/            # MCP resources
├── deploy/                       # Deployment scripts
│   ├── multi-tenant-server.py   # Multi-tenant server
│   ├── multi-tenant-deploy.sh   # Deployment script
│   ├── aws-deploy.sh            # AWS deployment
│   ├── terraform/               # Infrastructure as code
│   └── docker/                  # Docker deployment
├── docs/                        # Documentation
├── requirements.txt             # Python dependencies
├── pyproject.toml              # Project configuration
└── README.md                   # This file
```

## 🔧 Deployment Options

### Option 1: Multi-Tenant Server (Recommended)

**Best for**: Multiple users, maximum security

```bash
# Deploy multi-tenant server
./deploy/multi-tenant-deploy.sh

# Each user authenticates with their own credentials
# No shared credentials or data access
```

### Option 2: Single-Tenant Server

**Best for**: Personal use only

```bash
# Deploy single-tenant server
./deploy/secure-deploy.sh

# Configure with your Canvas credentials
sudo /opt/canvas-mcp/manage-credentials.sh setup
```

### Option 3: Docker Deployment

**Best for**: Containerized environments

```bash
# Build and run with Docker
cd deploy/docker
docker-compose up -d
```

### Option 4: Infrastructure as Code

**Best for**: Production deployments

```bash
# Deploy with Terraform
cd deploy/terraform
terraform init
terraform plan
terraform apply
```

## 🔐 Security Models

### Multi-Tenant (Recommended)
- ✅ Each user provides their own Canvas credentials
- ✅ Complete data isolation between users
- ✅ Proper audit trails
- ✅ FERPA compliant

### Single-Tenant
- ⚠️ Shared credentials (security risk)
- ⚠️ All users see the same data
- ✅ Simple setup

## 📖 Documentation

- [Quick Start Guide](deploy/QUICK-START.md)
- [Security Model](deploy/SECURITY-MODEL.md)
- [AWS Deployment](deploy/README.md)
- [User Guide](deploy/USER-GUIDE.md)

## 🛠️ Management Commands

### Service Management
```bash
# Start/stop/restart service
sudo systemctl start|stop|restart canvas-mcp-multi-tenant

# Check status
sudo systemctl status canvas-mcp-multi-tenant

# View logs
sudo journalctl -u canvas-mcp-multi-tenant -f
```

### Monitoring
```bash
# Check server status
sudo /opt/canvas-mcp-multi-tenant/monitor.sh

# Clean up expired sessions
sudo /opt/canvas-mcp-multi-tenant/cleanup-sessions.sh
```

## 🔧 Configuration

### Environment Variables

```bash
# Multi-tenant server (no credentials needed)
# Users authenticate with their own credentials

# Single-tenant server
CANVAS_API_TOKEN=your_canvas_token
CANVAS_API_URL=https://your-school.canvas.edu/api/v1
INSTITUTION_NAME=Your School Name
```

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u canvas-mcp-multi-tenant -f
   ```

2. **Authentication failed**
   - Check Canvas API token
   - Verify Canvas URL format
   - Ensure API access is enabled

3. **Permission denied**
   ```bash
   sudo chown -R canvas-mcp:canvas-mcp /opt/canvas-mcp-multi-tenant
   ```

### Log Locations

- **System logs**: `/var/log/syslog`
- **Service logs**: `journalctl -u canvas-mcp-multi-tenant`
- **Application logs**: `/var/log/canvas-mcp-multi-tenant/`

## 📊 Monitoring

### Health Checks
```bash
# Check service health
sudo systemctl is-active canvas-mcp-multi-tenant

# Monitor resources
sudo /opt/canvas-mcp-multi-tenant/monitor.sh
```

### CloudWatch Integration
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

## 🔄 Updates

### Update Application
```bash
# SSH to EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Update code
cd canvas-mcp
git pull origin main

# Restart service
sudo systemctl restart canvas-mcp-multi-tenant
```

## 📞 Support

### Getting Help

1. **Check logs**: `sudo journalctl -u canvas-mcp-multi-tenant -f`
2. **Verify service**: `sudo systemctl status canvas-mcp-multi-tenant`
3. **Test authentication**: Use the authenticate_canvas tool
4. **Check permissions**: Ensure proper file ownership

### Useful Commands

```bash
# Full system status
sudo systemctl status canvas-mcp-multi-tenant
sudo /opt/canvas-mcp-multi-tenant/monitor.sh

# View all logs
sudo journalctl -u canvas-mcp-multi-tenant --since "1 hour ago"
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**⚠️ Security Notice**: This server handles sensitive educational data. Please ensure proper security measures are in place before deployment.