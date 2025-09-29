# 🔒 Secure Canvas MCP Server - Production Ready

## 🛡️ **Enterprise-Grade Security & Privacy**

This is a **production-ready, secure Canvas MCP server** with comprehensive security and privacy protections.

### **🔐 Security Features**
- ✅ **Multi-tenant architecture**: Each user provides their own Canvas credentials
- ✅ **Session isolation**: Complete user session isolation
- ✅ **FERPA compliance**: Built-in data anonymization and privacy protection
- ✅ **Rate limiting**: 60 requests per minute per session
- ✅ **Input validation**: All inputs validated and sanitized
- ✅ **Path traversal protection**: Prevents directory traversal attacks
- ✅ **Secure error handling**: No sensitive data in error messages
- ✅ **Automatic session cleanup**: Expired sessions automatically removed

### **🔒 Privacy Protection**
- ✅ **Data anonymization**: All PII is anonymized before transmission
- ✅ **No credential sharing**: Zero risk of credential exposure between users
- ✅ **Secure session management**: 24-hour session timeout with automatic cleanup
- ✅ **HTTPS enforcement**: All Canvas API requests use HTTPS
- ✅ **Request size limits**: Prevents large payload attacks

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
pip install httpx
```

### **2. Run the Secure Server**
```bash
python deploy/multi-tenant-server-secure.py
```

### **3. Configure Claude Desktop**
Add to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "canvas-mcp-multi-tenant": {
      "command": "ssh",
      "args": [
        "-o", "ServerAliveInterval=15",
        "-o", "ServerAliveCountMax=3",
        "-o", "TCPKeepAlive=yes",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "LogLevel=ERROR",
        "-i", "/path/to/your/key.pem",
        "ec2-user@your-instance.amazonaws.com",
        "bash -c 'cd /path/to/canvas-mcp && export PYTHONPATH=/path/to/site-packages && exec python3.11 deploy/multi-tenant-server-secure.py'"
      ]
    }
  }
}
```

## 📚 **Available Tools**

### **Authentication & Profile**
- `authenticate_canvas` - Authenticate with your Canvas credentials
- `get_my_profile` - Get your Canvas profile information
- `get_session_info` - Check your current session status
- `logout` - Logout and invalidate your session

### **Courses**
- `list_my_courses` - List all your courses
- `get_course_details` - Get detailed information about a specific course
- `search_courses` - Search for courses by name or code

### **Assignments**
- `list_assignments` - List assignments for a specific course
- `get_assignment_details` - Get detailed information about a specific assignment

### **Discussions & Announcements**
- `list_discussions` - List discussions for a specific course
- `get_discussion_details` - Get detailed information about a specific discussion
- `list_announcements` - List announcements for a specific course

### **Grades & Calendar**
- `get_grades` - Get your grades for a specific course
- `list_calendar_events` - List calendar events for a specific course

## 🔒 **Security Configuration**

### **Rate Limiting**
- **Requests per minute**: 60 requests per session
- **Session limit**: 5 concurrent sessions per user
- **Timeout**: 30 seconds per API request

### **Session Management**
- **Session timeout**: 24 hours
- **Automatic cleanup**: Expired sessions are automatically removed
- **Secure session IDs**: 32-byte cryptographically secure random tokens

### **Input Validation**
- **Character filtering**: Removes dangerous characters
- **Length limits**: Maximum 1000 characters per input
- **Endpoint validation**: Prevents path traversal attacks

## 🚫 **What's NOT Exposed**

### **Never Exposed to Other Users**
- ❌ **Your Canvas API tokens**
- ❌ **Your Canvas API URLs**
- ❌ **Your personal information** (names, emails, login IDs)
- ❌ **Your course materials**
- ❌ **Your grades or academic records**
- ❌ **Your session data**

### **Never Exposed to the Internet**
- ❌ **Server-side credential storage**
- ❌ **Unencrypted data transmission**
- ❌ **Sensitive error messages**
- ❌ **User session details**

## 🛡️ **Privacy Compliance**

### **FERPA Compliance**
- ✅ **Student data anonymization**: All PII is anonymized
- ✅ **Data isolation**: No cross-user data access
- ✅ **Secure transmission**: All data encrypted in transit
- ✅ **Access controls**: Per-user authentication required

### **Security Best Practices**
- ✅ **Defense in depth**: Multiple security layers
- ✅ **Least privilege**: Minimal required permissions
- ✅ **Secure by default**: Security features enabled by default
- ✅ **Regular cleanup**: Automatic session and data cleanup

## 🔧 **Production Deployment**

### **AWS EC2 Deployment**
1. **Launch EC2 instance** with appropriate security groups
2. **Install Python 3.11** and required dependencies
3. **Upload server files** to the instance
4. **Configure systemd service** for automatic startup
5. **Set up monitoring** and logging

### **Security Checklist**
- ✅ **HTTPS only** for all connections
- ✅ **Firewall rules** to restrict access
- ✅ **Monitor server logs** for security events
- ✅ **Regular security updates** of dependencies
- ✅ **Backup and recovery** procedures in place

## 📋 **Usage Examples**

### **Authentication**
```
Can you help me authenticate with Canvas? I need to use the authenticate_canvas tool with my Canvas credentials.
```

### **List Courses**
```
Show me my Canvas courses using the list_my_courses tool.
```

### **Get Assignments**
```
List assignments for course ID 12345 using the list_assignments tool.
```

### **Check Grades**
```
Show me my grades for course ID 12345 using the get_grades tool.
```

## 🚨 **Security Warnings**

### **For Users**
1. **Never share your Canvas API token** with others
2. **Use strong, unique API tokens** for each application
3. **Logout when finished** to invalidate your session
4. **Report any suspicious activity** immediately

### **For Administrators**
1. **Monitor session activity** for unusual patterns
2. **Review rate limiting logs** for potential abuse
3. **Ensure HTTPS is enforced** for all connections
4. **Regular security updates** of dependencies

## 📞 **Support**

For security issues or questions:
1. **Check the security review**: `SECURITY-REVIEW.md`
2. **Review server logs** for error messages
3. **Test the server manually** to verify functionality
4. **Contact system administrator** for production issues

---

**This server implements enterprise-grade security and privacy protections to ensure your Canvas data remains secure and private.**
