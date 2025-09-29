# 🔒 SECURE Canvas MCP Server

**Enterprise-grade security with FERPA compliance**

A secure Canvas MCP server that provides Claude Desktop with access to Canvas LMS functionality while maintaining the highest security standards.

## 🛡️ Security Features

### Enterprise-Grade Security
- **SSL/TLS Encryption**: All communication encrypted with certificate verification
- **Session Isolation**: Complete user data separation, no cross-user access
- **Token Encryption**: PBKDF2-HMAC with 100,000 iterations and cryptographic salt
- **No Persistent Storage**: Tokens never stored on disk, memory-only with cleanup
- **Rate Limiting**: 60 requests per minute per session protection
- **Input Validation**: API tokens validated before use
- **Automatic Cleanup**: Sessions expire after 1 hour of inactivity

### FERPA Compliance
- **Data Isolation**: Student data isolated per session
- **No Cross-User Access**: Impossible to access other users' data
- **Secure Transmission**: All data encrypted in transit
- **Access Logging**: Session activity tracked
- **Data Retention**: Automatic cleanup of expired data

## 🚀 Quick Start

### 1. Deploy to AWS

```bash
# Make deployment script executable
chmod +x deploy-secure.sh

# Deploy to your AWS instance
./deploy-secure.sh /path/to/your/aws-key.pem ec2-user@your-aws-instance.com
```

### 2. Configure Claude Desktop

The deployment script generates a `claude_desktop_config.json` file. Copy it to:

```bash
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/
```

### 3. Restart Claude Desktop

Restart Claude Desktop to load the new MCP server configuration.

## 📚 Usage

### Authentication

First, authenticate with your Canvas account using the `authenticate_canvas` tool:

- **api_token**: Your Canvas API token (found in Canvas Account Settings)
- **api_url**: Your Canvas API URL (e.g., https://your-school.canvas.edu/api/v1)
- **institution_name**: Your institution name (optional)

### Available Tools

- **`authenticate_canvas`** - Authenticate with Canvas using your credentials
- **`logout`** - Securely logout and clear all authentication data
- **`list_courses`** - List all your courses from Canvas
- **`list_assignments`** - List assignments for a specific course
- **`get_assignments_due_tomorrow`** - Get assignments due tomorrow

## 🔒 Security Guarantees

### Your Canvas Token is Protected Because:

1. **In Transit**: SSL/TLS + SSH encryption prevents interception
2. **On Server**: PBKDF2-HMAC encrypted in isolated session prevents access
3. **From Other Users**: Complete session isolation prevents cross-user access
4. **From Persistence**: No disk storage, memory-only with cleanup prevents data leaks
5. **From Abuse**: Rate limiting and input validation prevent attacks

### Technical Security Implementation

- **Encryption**: PBKDF2-HMAC with 100,000 iterations and cryptographic salt
- **Session Management**: UUID4-based session IDs with thread-safe access
- **Memory Management**: Automatic garbage collection on session destruction
- **Network Security**: SSL context with certificate verification
- **Access Control**: Session-based authentication with automatic expiry

## 🏗️ Architecture

### Components

- **SecureSessionManager**: Manages user sessions with isolation
- **SecureTokenManager**: Handles token encryption/decryption
- **SecureCanvasClient**: Makes secure API requests with rate limiting
- **FastMCP Server**: Provides MCP protocol interface

### Data Flow

1. User authenticates → Session created with encrypted token
2. Tool calls → Session automatically detected and used
3. API requests → Token decrypted, request made with SSL verification
4. Session expiry → Automatic cleanup of all data

## 📋 Requirements

- **Python**: 3.11+
- **Dependencies**: fastmcp, httpx
- **AWS Instance**: EC2 with SSH access
- **Claude Desktop**: Latest version

## 🔧 Configuration

### AWS Instance Setup

1. **Security Groups**: Ensure port 22 (SSH) is open
2. **Python 3.11+**: Install if not available
3. **Dependencies**: Install fastmcp and httpx

### Claude Desktop Configuration

The deployment script automatically generates the correct configuration for your AWS instance.

## 🔍 Troubleshooting

### Common Issues

1. **"Server disconnected"**
   - Check SSH connection to AWS instance
   - Verify Python 3.11+ is installed
   - Check if dependencies are installed

2. **"Authentication failed"**
   - Verify Canvas API token is correct
   - Check Canvas API URL format
   - Ensure token has proper permissions

3. **"Rate limit exceeded"**
   - Wait 1 minute before making more requests
   - This is a security feature to prevent abuse

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export DEBUG=1
```

## 🔄 Updates

To update the server:

1. Pull latest changes from repository
2. Run deployment script again
3. Restart Claude Desktop

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Verify all prerequisites are met
3. Ensure AWS instance is accessible
4. Check Claude Desktop configuration

## 🎯 Production Ready

This implementation is **PRODUCTION READY** with:
- Enterprise-grade security
- FERPA compliance
- Complete user isolation
- Strong encryption
- Abuse protection
- Automatic cleanup

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines and code of conduct.

## 📚 Documentation

- [Installation Guide](SECURE-INSTALLATION.md)
- [Security Audit](SECURITY-SUMMARY.md)
- [API Documentation](docs/)

---

**🔒 Your Canvas token is fully protected with enterprise-grade security!**
