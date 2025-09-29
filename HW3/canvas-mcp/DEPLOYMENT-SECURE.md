# 🚀 Secure Deployment Guide

## Overview

This guide provides step-by-step instructions for securely deploying the Canvas MCP Server with enterprise-grade security and privacy protection.

## 🔐 Security Prerequisites

### **Required Security Measures**
- [ ] SSL/TLS certificates (Let's Encrypt recommended)
- [ ] Firewall configuration (restrictive access)
- [ ] Secure credential storage
- [ ] Regular security updates
- [ ] Monitoring and logging

### **Environment Setup**
```bash
# Create secure environment file
cp .env.template .env

# Edit with your credentials (NEVER commit .env to git)
nano .env
```

## 🏗️ Deployment Options

### **Option 1: AWS EC2 (Recommended)**

#### **Step 1: Launch EC2 Instance**
```bash
# Launch t3.micro instance with:
# - Amazon Linux 2023
# - Security group with SSH (22) and HTTPS (443)
# - IAM role with necessary permissions
```

#### **Step 2: Configure Security Groups**
```bash
# Inbound Rules:
# - SSH (22): Your IP only
# - HTTPS (443): 0.0.0.0/0 (for public access)
# - HTTP (80): 0.0.0.0/0 (for Let's Encrypt)

# Outbound Rules:
# - All traffic: 0.0.0.0/0
```

#### **Step 3: Deploy Application**
```bash
# SSH to instance
ssh -i your-key.pem ec2-user@your-ec2-ip

# Clone repository
git clone https://github.com/your-username/canvas-mcp.git
cd canvas-mcp

# Deploy multi-tenant server
chmod +x deploy/multi-tenant-deploy.sh
./deploy/multi-tenant-deploy.sh
```

### **Option 2: Docker Deployment**

#### **Step 1: Prepare Environment**
```bash
# Create environment file
cp .env.template .env
nano .env

# Build and run
docker-compose -f deploy/docker-compose-production.yml up -d
```

### **Option 3: Local Development**

#### **Step 1: Setup Environment**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
nano .env
```

## 🔒 Security Configuration

### **SSL/TLS Setup**

#### **Let's Encrypt (Recommended)**
```bash
# Install Certbot
sudo dnf install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo systemctl enable certbot-renew.timer
```

#### **Self-Signed Certificate (Development Only)**
```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Configure Nginx
# See deploy/nginx-production.conf
```

### **Firewall Configuration**

#### **UFW (Ubuntu/Debian)**
```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTPS
sudo ufw allow 443

# Allow HTTP (for Let's Encrypt)
sudo ufw allow 80

# Check status
sudo ufw status
```

#### **Firewalld (CentOS/RHEL/Amazon Linux)**
```bash
# Enable firewalld
sudo systemctl enable firewalld
sudo systemctl start firewalld

# Allow services
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=http

# Reload
sudo firewall-cmd --reload
```

### **Credential Management**

#### **Option A: Environment Variables (Simple)**
```bash
# Create .env file
cat > .env << EOF
CANVAS_API_TOKEN=your_actual_token_here
CANVAS_API_URL=https://your-institution.canvas.edu/api/v1
INSTITUTION_NAME=Your Institution
EOF

# Secure the file
chmod 600 .env
```

#### **Option B: AWS Secrets Manager (Enterprise)**
```bash
# Store credentials
aws secretsmanager create-secret \
    --name "canvas-mcp-credentials" \
    --secret-string '{"api_token":"your-token","api_url":"https://..."}'

# Retrieve in application
aws secretsmanager get-secret-value \
    --secret-id canvas-mcp-credentials \
    --query SecretString --output text
```

## 🔍 Security Monitoring

### **Log Configuration**
```bash
# Security logs
sudo mkdir -p /var/log/canvas-mcp
sudo touch /var/log/canvas-mcp-security.log
sudo chown canvas-mcp:canvas-mcp /var/log/canvas-mcp-security.log

# Application logs
sudo touch /var/log/canvas-mcp-server.log
sudo chown canvas-mcp:canvas-mcp /var/log/canvas-mcp-server.log
```

### **Monitoring Commands**
```bash
# Check service status
sudo systemctl status canvas-mcp-multi-tenant

# View logs
sudo journalctl -u canvas-mcp-multi-tenant -f

# Security logs
sudo tail -f /var/log/canvas-mcp-security.log

# Check SSL certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

## 🚨 Security Checklist

### **Pre-Deployment**
- [ ] Remove all hardcoded credentials
- [ ] Configure secure environment variables
- [ ] Set up SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Enable security logging
- [ ] Set up monitoring

### **Post-Deployment**
- [ ] Test authentication flows
- [ ] Verify data anonymization
- [ ] Check rate limiting
- [ ] Monitor security logs
- [ ] Test SSL certificate
- [ ] Verify CORS configuration
- [ ] Run security scan

### **Ongoing Security**
- [ ] Regular security updates
- [ ] Monitor logs for anomalies
- [ ] Review access patterns
- [ ] Update dependencies
- [ ] Conduct security audits

## 🔧 Troubleshooting

### **Common Issues**

#### **SSL Certificate Issues**
```bash
# Check certificate
openssl x509 -in /etc/letsencrypt/live/your-domain.com/cert.pem -text -noout

# Renew certificate
sudo certbot renew --dry-run
```

#### **Service Not Starting**
```bash
# Check logs
sudo journalctl -u canvas-mcp-multi-tenant -f

# Check configuration
sudo systemctl cat canvas-mcp-multi-tenant

# Restart service
sudo systemctl restart canvas-mcp-multi-tenant
```

#### **Permission Issues**
```bash
# Fix ownership
sudo chown -R canvas-mcp:canvas-mcp /opt/canvas-mcp

# Fix permissions
sudo chmod 600 /opt/canvas-mcp/.env
sudo chmod 755 /opt/canvas-mcp/deploy/multi-tenant-server-secure.py
```

## 📚 Additional Resources

- [Security Guide](SECURITY.md) - Comprehensive security documentation
- [Production Deployment](deploy/PRODUCTION-DEPLOYMENT.md) - Production-specific guidance
- [Security Audit Report](deploy/SECURITY-FINAL-AUDIT.md) - Security audit results
- [Installation Guide](deploy/INSTALLATION-GUIDE.md) - Step-by-step installation

## 🆘 Support

For security issues or questions:
- Create a GitHub issue with "security" label
- Do not include sensitive information in public issues
- For critical issues, contact maintainers directly

---

**Remember**: Security is an ongoing process. Regularly update dependencies, monitor logs, and conduct security reviews.
