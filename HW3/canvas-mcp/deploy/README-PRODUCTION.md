# 🔒 Canvas MCP Server - Production Edition

## 🛡️ **Enterprise-Grade Security & Privacy**

A production-ready Canvas MCP server with enterprise-grade security features, designed for educational institutions and organizations that require FERPA compliance and data privacy.

### **🚀 Quick Start**

```bash
# 1. Clone the repository
git clone https://github.com/your-username/canvas-mcp.git
cd canvas-mcp

# 2. Run the production installation script
sudo bash deploy/install-production.sh
```

### **🔒 Security Features**

- **Multi-tenant architecture**: Each user provides their own Canvas credentials
- **Session isolation**: User sessions are completely isolated
- **FERPA compliance**: Built-in data anonymization and privacy protection
- **Real SSL certificates**: Let's Encrypt integration with auto-renewal
- **Security logging**: Comprehensive audit trail
- **Rate limiting**: IP and session-based rate limiting
- **Input validation**: All inputs are validated and sanitized
- **Secure error handling**: No sensitive data exposure

---

## 📚 **API Documentation**

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

## 🐳 **Docker Deployment**

### **1. Build and Run**

```bash
# Build the image
docker build -f deploy/Dockerfile-production -t canvas-mcp-server .

# Run with Docker Compose
docker-compose -f deploy/docker-compose-production.yml up -d
```

### **2. Environment Variables**

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
