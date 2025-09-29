# Canvas MCP Server - AWS Deployment Guide

This guide provides multiple deployment options for running the Canvas MCP Server on AWS.

## 🚀 Deployment Options

### Option 1: EC2 Instance (Recommended)
- **Cost**: ~$5-10/month (t3.micro)
- **Control**: Full control over the environment
- **Security**: Complete isolation

### Option 2: Docker on EC2
- **Cost**: ~$5-10/month (t3.micro)
- **Benefits**: Containerized, easy updates
- **Security**: Container isolation

### Option 3: AWS ECS/Fargate
- **Cost**: ~$10-20/month
- **Benefits**: Serverless, auto-scaling
- **Complexity**: Higher setup complexity

## 📋 Prerequisites

1. **AWS Account** with appropriate permissions
2. **Terraform** (for infrastructure as code)
3. **Docker** (for containerized deployment)
4. **Your Canvas API credentials**

## 🔧 Quick Start - EC2 Instance

### Step 1: Launch EC2 Instance

```bash
# Using AWS CLI
aws ec2 run-instances \
    --image-id ami-0c02fb55956c7d316 \
    --instance-type t3.micro \
    --key-name your-key-pair \
    --security-group-ids sg-xxxxxxxxx \
    --user-data file://deploy/terraform/user-data.sh
```

### Step 2: Connect and Deploy

```bash
# SSH to your instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Run the setup script
sudo /home/ubuntu/setup-canvas-mcp.sh

# Edit configuration
sudo nano /opt/canvas-mcp/.env
```

### Step 3: Configure Canvas Credentials

Edit `/opt/canvas-mcp/.env`:

```bash
CANVAS_API_TOKEN=your_actual_canvas_token
CANVAS_API_URL=https://your-school.canvas.edu/api/v1
INSTITUTION_NAME=Your School Name
```

### Step 4: Start the Service

```bash
sudo systemctl start canvas-mcp-server
sudo systemctl status canvas-mcp-server
sudo journalctl -u canvas-mcp-server -f
```

## 🐳 Docker Deployment

### Step 1: Build and Run

```bash
# Build the image
docker build -f deploy/docker/Dockerfile -t canvas-mcp-server .

# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Run with docker-compose
cd deploy/docker
docker-compose up -d
```

### Step 2: Monitor

```bash
# Check logs
docker-compose logs -f

# Check status
docker-compose ps
```

## 🏗️ Infrastructure as Code (Terraform)

### Step 1: Configure Terraform

```bash
cd deploy/terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars
cat > terraform.tfvars << EOF
aws_region = "us-east-1"
instance_type = "t3.micro"
allocate_eip = true
create_key_pair = true
public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC..."
EOF
```

### Step 2: Deploy Infrastructure

```bash
# Plan deployment
terraform plan

# Apply configuration
terraform apply
```

### Step 3: Configure Application

```bash
# Get the public IP
terraform output public_ip

# SSH to instance
ssh -i canvas-mcp-key.pem ubuntu@$(terraform output -raw public_ip)

# Configure the application
sudo nano /opt/canvas-mcp/.env
sudo systemctl start canvas-mcp-server
```

## 🔐 Security Best Practices

### 1. Credential Management

**Option A: Environment Variables (Simple)**
```bash
# Store in .env file (secure the file)
chmod 600 /opt/canvas-mcp/.env
```

**Option B: AWS Systems Manager Parameter Store (Recommended)**
```bash
# Store credentials in AWS Parameter Store
aws ssm put-parameter \
    --name "/canvas-mcp/api-token" \
    --value "your-token" \
    --type "SecureString"

# Retrieve in your application
aws ssm get-parameter \
    --name "/canvas-mcp/api-token" \
    --with-decryption
```

**Option C: AWS Secrets Manager (Most Secure)**
```bash
# Store credentials in AWS Secrets Manager
aws secretsmanager create-secret \
    --name "canvas-mcp-credentials" \
    --secret-string '{"api_token":"your-token","api_url":"https://..."}'
```

### 2. Network Security

- **Security Groups**: Only allow necessary ports (SSH, MCP port)
- **VPC**: Use private subnets for the application
- **WAF**: Consider AWS WAF for additional protection

### 3. Monitoring and Logging

```bash
# Set up CloudWatch logging
sudo apt-get install -y awscli
aws logs create-log-group --log-group-name /aws/ec2/canvas-mcp-server
```

## 📊 Monitoring Setup

### CloudWatch Integration

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure CloudWatch
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

### Health Checks

```bash
# Create health check script
cat > /opt/canvas-mcp/health-check.sh << 'EOF'
#!/bin/bash
if systemctl is-active --quiet canvas-mcp-server; then
    echo "Service is running"
    exit 0
else
    echo "Service is not running"
    exit 1
fi
EOF

chmod +x /opt/canvas-mcp/health-check.sh
```

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# SSH to your instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update code
cd /opt/canvas-mcp
git pull origin main

# Restart service
sudo systemctl restart canvas-mcp-server
```

### Backup Strategy

```bash
# Backup configuration
tar -czf canvas-mcp-backup-$(date +%Y%m%d).tar.gz /opt/canvas-mcp/.env

# Store in S3
aws s3 cp canvas-mcp-backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

## 💰 Cost Optimization

### EC2 Instance Sizing

- **t3.micro**: Free tier eligible, good for testing
- **t3.small**: ~$15/month, better performance
- **t3.medium**: ~$30/month, production ready

### Reserved Instances

For production use, consider Reserved Instances for 30-60% savings.

## 🚨 Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u canvas-mcp-server -f
   ```

2. **Permission denied**
   ```bash
   sudo chown -R canvas-mcp:canvas-mcp /opt/canvas-mcp
   ```

3. **API connection issues**
   ```bash
   # Test API connection
   canvas-mcp-server --test
   ```

### Log Locations

- **System logs**: `/var/log/syslog`
- **Service logs**: `journalctl -u canvas-mcp-server`
- **Application logs**: `/var/log/canvas-mcp-server/`

## 📞 Support

For issues with this deployment:

1. Check the logs first
2. Verify your Canvas API credentials
3. Ensure security groups allow necessary traffic
4. Check AWS CloudWatch for additional insights
