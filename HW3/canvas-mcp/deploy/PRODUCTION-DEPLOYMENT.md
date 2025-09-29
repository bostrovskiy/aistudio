# 🚀 Canvas MCP Server - Production Deployment Guide

## 🔒 **Enterprise-Grade Security & Privacy**

This guide shows how to deploy the Canvas MCP server with enterprise-grade security features for production use.

### **🛡️ Security Features**

- **Multi-tenant architecture**: Each user provides their own Canvas credentials
- **Session isolation**: User sessions are completely isolated
- **FERPA compliance**: Built-in data anonymization and privacy protection
- **Real SSL certificates**: Let's Encrypt integration with auto-renewal
- **Security logging**: Comprehensive audit trail
- **Rate limiting**: IP and session-based rate limiting
- **Input validation**: All inputs are validated and sanitized
- **Secure error handling**: No sensitive data exposure

---

## 🚀 **Quick Start**

### **1. Prerequisites**

- Linux server (Ubuntu 20.04+, Amazon Linux 2, or CentOS 7+)
- Python 3.11+
- Nginx
- Domain name (for SSL certificate)

### **2. Installation**

```bash
# Clone the repository
git clone https://github.com/your-username/canvas-mcp.git
cd canvas-mcp

# Install dependencies
pip install -r deploy/requirements-http.txt

# Make scripts executable
chmod +x deploy/*.sh
```

### **3. Configure Environment**

```bash
# Set environment variables
export HOST=0.0.0.0
export PORT=8080
export SECURITY_LOG_FILE=/var/log/canvas-mcp-security.log
export MAX_SESSIONS_PER_USER=5
export MAX_REQUESTS_PER_MINUTE=60
export MAX_REQUESTS_PER_IP_PER_MINUTE=100
export CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
```

### **4. Deploy Server**

```bash
# Start the production server
python deploy/mcp-http-server-production.py
```

### **5. Setup SSL Certificate**

```bash
# Run SSL setup script
sudo bash deploy/setup-ssl-production.sh
```

---

## 🌐 **API Endpoints**

### **Base URL**
- **HTTPS**: `https://yourdomain.com`

### **Authentication**
```http
POST /authenticate
Content-Type: application/json

{
  "api_token": "your_canvas_token",
  "api_url": "https://your-school.canvas.edu/api/v1",
  "institution_name": "Your School"
}
```

### **Available Endpoints**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server information |
| `/authenticate` | POST | Authenticate with Canvas |
| `/profile` | GET | Get user profile |
| `/courses` | GET | List courses |
| `/courses/{id}` | GET | Get course details |
| `/assignments` | GET | List assignments |
| `/assignments/{id}` | GET | Get assignment details |
| `/discussions` | GET | List discussions |
| `/discussions/{id}` | GET | Get discussion details |
| `/announcements` | GET | List announcements |
| `/grades` | GET | Get grades |
| `/calendar` | GET | List calendar events |
| `/search` | GET | Search courses |
| `/session` | GET | Check session status |
| `/logout` | POST | Logout |

---

## 🔧 **Configuration**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8080` | Server port |
| `SECURITY_LOG_FILE` | `/var/log/canvas-mcp-security.log` | Security log file |
| `MAX_SESSIONS_PER_USER` | `5` | Max sessions per user |
| `MAX_REQUESTS_PER_MINUTE` | `60` | Max requests per minute per session |
| `MAX_REQUESTS_PER_IP_PER_MINUTE` | `100` | Max requests per minute per IP |
| `CORS_ORIGINS` | `https://localhost,https://127.0.0.1` | Allowed CORS origins |

### **Security Settings**

The server includes comprehensive security features:

- **Rate Limiting**: Prevents abuse and DoS attacks
- **Input Validation**: All inputs are validated and sanitized
- **Data Anonymization**: FERPA-compliant data anonymization
- **Security Logging**: Comprehensive audit trail
- **Session Management**: Secure session handling with automatic cleanup

---

## 🐳 **Docker Deployment**

### **1. Build Image**

```bash
# Build the Docker image
docker build -f deploy/Dockerfile-http -t canvas-mcp-server .
```

### **2. Run Container**

```bash
# Run with environment variables
docker run -d \
  --name canvas-mcp \
  -p 8080:8080 \
  -e HOST=0.0.0.0 \
  -e PORT=8080 \
  -e SECURITY_LOG_FILE=/var/log/canvas-mcp-security.log \
  -v /var/log:/var/log \
  canvas-mcp-server
```

### **3. Docker Compose**

```bash
# Run with Docker Compose
docker-compose -f deploy/docker-compose-http.yml up -d
```

---

## 🔒 **Security Features**

### **1. Multi-Tenant Architecture**

Each user provides their own Canvas credentials:
- No credential sharing between users
- Complete session isolation
- Automatic session cleanup

### **2. Data Protection**

- **FERPA Compliance**: Built-in data anonymization
- **PII Filtering**: Automatic removal of sensitive information
- **Secure Error Handling**: No sensitive data exposure

### **3. Network Security**

- **HTTPS**: Real SSL certificates with auto-renewal
- **Security Headers**: HSTS, X-Frame-Options, etc.
- **CORS**: Properly configured cross-origin resource sharing

### **4. Monitoring & Logging**

- **Security Logging**: Comprehensive audit trail
- **Request Tracking**: All requests are logged
- **Rate Limiting**: IP and session-based limits

---

## 📊 **Usage Examples**

### **JavaScript/Web Apps**

```javascript
// Authenticate
const response = await fetch('https://yourdomain.com/authenticate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    api_token: 'your_canvas_token',
    api_url: 'https://your-school.canvas.edu/api/v1'
  })
});

const { session_id } = await response.json();

// Get courses
const courses = await fetch(`https://yourdomain.com/courses?session_id=${session_id}`);
```

### **Python**

```python
import requests

# Authenticate
response = requests.post('https://yourdomain.com/authenticate', json={
    'api_token': 'your_canvas_token',
    'api_url': 'https://your-school.canvas.edu/api/v1'
})

session_id = response.json()['session_id']

# Get courses
courses = requests.get(f'https://yourdomain.com/courses?session_id={session_id}')
```

### **Claude Desktop**

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "canvas-mcp-http": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Content-Type: application/json",
        "-d", "{\"api_token\":\"your_canvas_token\",\"api_url\":\"https://your-school.canvas.edu/api/v1\"}",
        "https://yourdomain.com/authenticate"
      ]
    }
  }
}
```

---

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **SSL Certificate Issues**:
   ```bash
   # Check certificate status
   certbot certificates
   
   # Renew certificate manually
   certbot renew
   ```

2. **Permission Issues**:
   ```bash
   # Fix log file permissions
   sudo touch /var/log/canvas-mcp-security.log
   sudo chown $USER:$USER /var/log/canvas-mcp-security.log
   ```

3. **Rate Limiting**:
   - Check security logs: `tail -f /var/log/canvas-mcp-security.log`
   - Adjust rate limits in environment variables

### **Debug Commands**

```bash
# Check server status
ps aux | grep mcp-http-server

# Check nginx status
sudo systemctl status nginx

# Check SSL certificate
curl -I https://yourdomain.com/

# View security logs
tail -f /var/log/canvas-mcp-security.log
```

---

## 📋 **Security Checklist**

- [ ] Real SSL certificate installed
- [ ] Security logging enabled
- [ ] Rate limiting configured
- [ ] CORS origins restricted
- [ ] Input validation enabled
- [ ] Data anonymization active
- [ ] Session management configured
- [ ] Error handling secure
- [ ] Monitoring setup
- [ ] Backup strategy

---

## 🆘 **Support**

For issues and questions:

1. Check the security logs: `/var/log/canvas-mcp-security.log`
2. Review the troubleshooting section above
3. Check nginx configuration: `nginx -t`
4. Verify SSL certificate: `certbot certificates`

---

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🔒 Your Canvas MCP server is now enterprise-grade secure and ready for production use!**
