# 🌐 Canvas MCP HTTP Server - Deployment Guide

## 🔒 **HTTP/HTTPS Endpoint for Canvas MCP Server**

This guide shows how to deploy the Canvas MCP server as an HTTP/HTTPS web service, making it accessible via REST API endpoints.

### **🚀 Quick Start**

#### **1. Local Development**
```bash
# Install dependencies
pip install -r requirements-http.txt

# Run the server
python mcp-http-server.py
```

#### **2. Docker Deployment**
```bash
# Build and run with Docker Compose
docker-compose -f docker-compose-http.yml up -d

# With Nginx reverse proxy for HTTPS
docker-compose -f docker-compose-http.yml --profile nginx up -d
```

#### **3. Production Deployment**
```bash
# Set environment variables
export HOST=0.0.0.0
export PORT=8000
export SSL_KEYFILE=/path/to/private.key
export SSL_CERTFILE=/path/to/certificate.crt

# Run the server
python mcp-http-server.py
```

## 📚 **API Endpoints**

### **Base URL**
- **HTTP**: `http://localhost:8000`
- **HTTPS**: `https://your-domain.com`

### **Available Endpoints**

#### **Authentication**
```http
POST /authenticate
Content-Type: application/json

{
  "api_token": "your_canvas_token",
  "api_url": "https://your-school.canvas.edu/api/v1",
  "institution_name": "Your School"
}
```

#### **Profile Information**
```http
GET /profile?session_id=your_session_id
```

#### **Courses**
```http
GET /courses?session_id=your_session_id&include_concluded=false
GET /courses/{course_id}?session_id=your_session_id
```

#### **Assignments**
```http
GET /assignments?session_id=your_session_id&course_id=12345
GET /assignments/{assignment_id}?session_id=your_session_id&course_id=12345
```

#### **Discussions & Announcements**
```http
GET /discussions?session_id=your_session_id&course_id=12345&only_announcements=false
GET /discussions/{discussion_id}?session_id=your_session_id&course_id=12345
GET /announcements?session_id=your_session_id&course_id=12345
```

#### **Grades & Calendar**
```http
GET /grades?session_id=your_session_id&course_id=12345
GET /calendar?session_id=your_session_id&course_id=12345&start_date=2024-01-01&end_date=2024-12-31
```

#### **Search & Session Management**
```http
GET /search?session_id=your_session_id&search_term=math
GET /session?session_id=your_session_id
POST /logout
Content-Type: application/json
{"session_id": "your_session_id"}
```

## 🔧 **Configuration Options**

### **Environment Variables**
```bash
# Server configuration
HOST=0.0.0.0                    # Host to bind to
PORT=8000                       # Port to listen on

# SSL configuration (optional)
SSL_KEYFILE=/path/to/private.key
SSL_CERTFILE=/path/to/certificate.crt

# CORS configuration
CORS_ORIGINS=*                   # Comma-separated list of allowed origins
```

### **Docker Configuration**
```yaml
# docker-compose-http.yml
services:
  canvas-mcp-http:
    build:
      context: .
      dockerfile: Dockerfile-http
    ports:
      - "8000:8000"
    environment:
      - HOST=0.0.0.0
      - PORT=8000
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

## 🛡️ **Security Features**

### **Built-in Security**
- ✅ **Multi-tenant architecture**: Each user provides their own credentials
- ✅ **Session isolation**: User sessions are completely isolated
- ✅ **Rate limiting**: 60 requests per minute per session
- ✅ **Input validation**: All inputs are validated and sanitized
- ✅ **Data anonymization**: FERPA-compliant data protection
- ✅ **HTTPS support**: SSL/TLS encryption for secure communication
- ✅ **CORS configuration**: Configurable cross-origin resource sharing

### **Production Security**
- ✅ **Nginx reverse proxy**: For SSL termination and load balancing
- ✅ **Security headers**: HSTS, X-Frame-Options, etc.
- ✅ **SSL/TLS configuration**: Modern cipher suites and protocols
- ✅ **Health checks**: Automatic health monitoring
- ✅ **Logging**: Comprehensive request and error logging

## 🚀 **Deployment Options**

### **1. Local Development**
```bash
# Install dependencies
pip install -r requirements-http.txt

# Run the server
python mcp-http-server.py
```

### **2. Docker Deployment**
```bash
# Build the image
docker build -f Dockerfile-http -t canvas-mcp-http .

# Run the container
docker run -p 8000:8000 canvas-mcp-http
```

### **3. Docker Compose (Recommended)**
```bash
# Start the service
docker-compose -f docker-compose-http.yml up -d

# With Nginx for HTTPS
docker-compose -f docker-compose-http.yml --profile nginx up -d
```

### **4. Production Deployment**
```bash
# Set up SSL certificates
mkdir -p ssl
cp your-private.key ssl/private.key
cp your-certificate.crt ssl/certificate.crt

# Configure environment
export SSL_KEYFILE=/app/ssl/private.key
export SSL_CERTFILE=/app/ssl/certificate.crt

# Run with Docker Compose
docker-compose -f docker-compose-http.yml --profile nginx up -d
```

## 📊 **Monitoring & Logging**

### **Health Checks**
```bash
# Check server health
curl http://localhost:8000/

# Check with Nginx
curl http://localhost/health
```

### **Logs**
```bash
# View application logs
docker-compose -f docker-compose-http.yml logs -f canvas-mcp-http

# View Nginx logs
docker-compose -f docker-compose-http.yml logs -f nginx
```

## 🔐 **SSL/TLS Configuration**

### **Generate SSL Certificates**
```bash
# Self-signed certificate (development)
openssl req -x509 -newkey rsa:4096 -keyout ssl/private.key -out ssl/certificate.crt -days 365 -nodes

# Let's Encrypt certificate (production)
certbot certonly --standalone -d your-domain.com
```

### **Nginx SSL Configuration**
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
}
```

## 📱 **Client Integration**

### **JavaScript/Node.js**
```javascript
// Authenticate
const response = await fetch('https://your-domain.com/authenticate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    api_token: 'your_canvas_token',
    api_url: 'https://your-school.canvas.edu/api/v1'
  })
});

const { session_id } = await response.json();

// Get courses
const courses = await fetch(`https://your-domain.com/courses?session_id=${session_id}`);
```

### **Python**
```python
import requests

# Authenticate
response = requests.post('https://your-domain.com/authenticate', json={
    'api_token': 'your_canvas_token',
    'api_url': 'https://your-school.canvas.edu/api/v1'
})
session_id = response.json()['session_id']

# Get courses
courses = requests.get(f'https://your-domain.com/courses?session_id={session_id}')
```

### **cURL Examples**
```bash
# Authenticate
curl -X POST https://your-domain.com/authenticate \
  -H "Content-Type: application/json" \
  -d '{"api_token": "your_token", "api_url": "https://your-school.canvas.edu/api/v1"}'

# Get courses
curl "https://your-domain.com/courses?session_id=your_session_id"
```

## 🚨 **Troubleshooting**

### **Common Issues**
1. **Port already in use**: Change the PORT environment variable
2. **SSL certificate errors**: Verify certificate paths and permissions
3. **CORS issues**: Configure CORS_ORIGINS environment variable
4. **Rate limiting**: Adjust rate limiting settings in the code

### **Debug Mode**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
python mcp-http-server.py
```

## 📋 **Production Checklist**

- ✅ **SSL certificates** configured and valid
- ✅ **Firewall rules** properly configured
- ✅ **Domain name** pointing to your server
- ✅ **Monitoring** and logging set up
- ✅ **Backup procedures** in place
- ✅ **Security headers** configured
- ✅ **Rate limiting** appropriate for your use case
- ✅ **Health checks** monitoring the service

---

**Your Canvas MCP server is now accessible via HTTP/HTTPS with enterprise-grade security!** 🎉
