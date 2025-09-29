# 🚀 Canvas MCP Server - AWS Quick Start Guide

This guide will help you deploy the Canvas MCP Server to AWS with secure credential management.

## 📋 Prerequisites

- AWS Account with appropriate permissions
- AWS CLI configured (`aws configure`)
- Your Canvas API credentials
- Basic familiarity with AWS EC2

## 🎯 Quick Deployment (5 minutes)

### Step 1: Launch EC2 Instance

```bash
# Launch a t3.micro instance (free tier eligible)
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t3.micro \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --user-data file://deploy/terraform/user-data.sh
```

### Step 2: Connect to Instance

```bash
# Get the public IP
aws ec2 describe-instances --query 'Reservations[*].Instances[*].PublicIpAddress' --output text

# SSH to your instance
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP
```

### Step 3: Deploy Application

```bash
# Clone the repository (or upload your code)
git clone https://github.com/your-repo/canvas-mcp.git
cd canvas-mcp

# Run the secure deployment script
chmod +x deploy/secure-deploy.sh
./deploy/secure-deploy.sh
```

### Step 4: Configure Credentials

```bash
# Set up your Canvas credentials securely
sudo /opt/canvas-mcp/manage-credentials.sh setup
```

### Step 5: Start Service

```bash
# Start the service
sudo systemctl start canvas-mcp-server

# Check status
sudo systemctl status canvas-mcp-server

# View logs
sudo journalctl -u canvas-mcp-server -f
```

## 🔐 Security Features

✅ **AWS Secrets Manager**: Credentials stored encrypted in AWS  
✅ **No Plaintext**: No credentials stored on disk  
✅ **IAM Access**: Role-based access control  
✅ **Encrypted Storage**: All secrets encrypted at rest  
✅ **Audit Trail**: All access logged in CloudTrail  

## 📊 Monitoring

### Check Service Status

```bash
# Service status
sudo systemctl status canvas-mcp-server

# Real-time logs
sudo journalctl -u canvas-mcp-server -f

# Test API connection
sudo /opt/canvas-mcp/venv/bin/canvas-mcp-server --test
```

### AWS CloudWatch Integration

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure monitoring
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## 🔧 Management Commands

### Credential Management

```bash
# Set up credentials (first time)
sudo /opt/canvas-mcp/manage-credentials.sh setup

# Test credential retrieval
sudo /opt/canvas-mcp/manage-credentials.sh test

# Update credentials
sudo /opt/canvas-mcp/manage-credentials.sh update

# Delete credentials
sudo /opt/canvas-mcp/manage-credentials.sh delete
```

### Service Management

```bash
# Start service
sudo systemctl start canvas-mcp-server

# Stop service
sudo systemctl stop canvas-mcp-server

# Restart service
sudo systemctl restart canvas-mcp-server

# Enable auto-start
sudo systemctl enable canvas-mcp-server

# Disable auto-start
sudo systemctl disable canvas-mcp-server
```

## 🐳 Docker Alternative

If you prefer Docker deployment:

```bash
# Build and run with Docker
cd deploy/docker
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🏗️ Infrastructure as Code

For production deployments, use Terraform:

```bash
cd deploy/terraform

# Initialize
terraform init

# Plan deployment
terraform plan

# Deploy infrastructure
terraform apply

# Get connection info
terraform output
```

## 💰 Cost Optimization

### Instance Sizing

| Instance Type | Monthly Cost | Use Case |
|---------------|--------------|----------|
| t3.micro | $0 (Free Tier) | Development/Testing |
| t3.small | ~$15 | Light Production |
| t3.medium | ~$30 | Production |
| t3.large | ~$60 | High Load |

### Reserved Instances

For production use, consider Reserved Instances for 30-60% savings:

```bash
# Purchase Reserved Instance
aws ec2 purchase-reserved-instances-offering \
    --reserved-instances-offering-id offering-12345678 \
    --instance-count 1
```

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u canvas-mcp-server -f
   ```

2. **Credential errors**
   ```bash
   sudo /opt/canvas-mcp/manage-credentials.sh test
   ```

3. **Permission denied**
   ```bash
   sudo chown -R canvas-mcp:canvas-mcp /opt/canvas-mcp
   ```

4. **AWS access issues**
   ```bash
   aws sts get-caller-identity
   ```

### Log Locations

- **System logs**: `/var/log/syslog`
- **Service logs**: `journalctl -u canvas-mcp-server`
- **Application logs**: `/var/log/canvas-mcp-server/`

## 🔄 Updates

### Update Application

```bash
# SSH to instance
ssh -i your-key.pem ubuntu@YOUR_INSTANCE_IP

# Update code
cd /opt/canvas-mcp
git pull origin main

# Restart service
sudo systemctl restart canvas-mcp-server
```

### Update Credentials

```bash
# Update credentials
sudo /opt/canvas-mcp/manage-credentials.sh update

# Restart service
sudo systemctl restart canvas-mcp-server
```

## 📞 Support

### Getting Help

1. **Check logs first**: `sudo journalctl -u canvas-mcp-server -f`
2. **Test credentials**: `sudo /opt/canvas-mcp/manage-credentials.sh test`
3. **Verify AWS access**: `aws sts get-caller-identity`
4. **Check service status**: `sudo systemctl status canvas-mcp-server`

### Useful Commands

```bash
# Full system status
sudo systemctl status canvas-mcp-server
sudo /opt/canvas-mcp/manage-credentials.sh test
aws sts get-caller-identity

# View all logs
sudo journalctl -u canvas-mcp-server --since "1 hour ago"

# Test API connection
sudo /opt/canvas-mcp/venv/bin/canvas-mcp-server --test
```

## ✅ Success Checklist

- [ ] EC2 instance launched and accessible
- [ ] Application deployed successfully
- [ ] Credentials stored in AWS Secrets Manager
- [ ] Service running and healthy
- [ ] Logs showing no errors
- [ ] API connection test passing
- [ ] Monitoring configured (optional)

## 🎉 You're Done!

Your Canvas MCP Server is now running securely on AWS with:

- ✅ Encrypted credential storage
- ✅ Automatic service management
- ✅ Comprehensive logging
- ✅ Easy updates and maintenance
- ✅ Cost-effective deployment

The server is ready to handle your Canvas API requests with full privacy protection!
