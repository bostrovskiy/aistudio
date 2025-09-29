# Multi-Tenant Canvas MCP Server - Installation Guide

## Overview

This is a **multi-tenant Canvas MCP Server** that allows each user to authenticate with their own Canvas credentials, providing secure, isolated access to Canvas LMS data.

## Key Features

- ✅ **Multi-tenant architecture**: Each user provides their own Canvas credentials
- ✅ **Secure authentication**: No shared credentials or security risks
- ✅ **Session management**: 24-hour session timeout with automatic cleanup
- ✅ **FERPA compliance**: Built-in data anonymization and privacy protection
- ✅ **Asyncio conflict resolution**: Subprocess approach prevents event loop conflicts

## Prerequisites

- Python 3.11+ (required for MCP compatibility)
- Canvas API access (institution-specific)
- SSH access to deployment server (for remote deployment)

## Dependencies

The server requires the following Python packages:

```
fastmcp>=0.1.0
httpx>=0.27.0
```

## Installation Methods

### Method 1: Direct Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd canvas-mcp
   ```

2. **Install dependencies**:
   ```bash
   pip install fastmcp httpx
   ```

3. **Run the server**:
   ```bash
   python deploy/multi-tenant-server-secure.py
   ```

### Method 2: AWS EC2 Deployment

1. **Connect to your EC2 instance**:
   ```bash
   ssh -i "your-key.pem" ec2-user@your-instance.amazonaws.com
   ```

2. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd canvas-mcp
   pip install fastmcp httpx
   ```

3. **Run the server**:
   ```bash
   python deploy/multi-tenant-server-secure.py
   ```

### Method 3: Systemd Service (Production)

1. **Install as systemd service**:
   ```bash
   sudo cp deploy/canvas-mcp-multi-tenant.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable canvas-mcp-multi-tenant
   sudo systemctl start canvas-mcp-multi-tenant
   ```

2. **Check status**:
   ```bash
   sudo systemctl status canvas-mcp-multi-tenant
   ```

## Configuration

### Claude Desktop Integration

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
        "bash -c 'cd /path/to/canvas-mcp && export PYTHONPATH=/path/to/site-packages && exec python3.11 deploy/multi-tenant-server.py'"
      ]
    }
  }
}
```

## Usage

### 1. Authentication

First, authenticate with your Canvas credentials:

```
authenticate_canvas(
  api_token="your-canvas-api-token",
  api_url="https://your-school.canvas.edu/api/v1",
  institution_name="Your Institution"
)
```

### 2. List Courses

```
list_my_courses(
  session_id="your-session-id",
  include_concluded=false
)
```

## Security Features

- **Per-user authentication**: Each user provides their own Canvas credentials
- **Session isolation**: User sessions are completely isolated
- **Automatic cleanup**: Expired sessions are automatically removed
- **No credential sharing**: No risk of credential exposure between users

## Troubleshooting

### Common Issues

1. **"Already running asyncio in this thread"**:
   - ✅ **Fixed**: The server uses a subprocess approach to avoid this issue

2. **"Server disconnected"**:
   - Check SSH connection settings
   - Verify Python path and dependencies
   - Ensure the server is running on the remote instance

3. **Authentication failures**:
   - Verify Canvas API token is valid
   - Check Canvas API URL is correct
   - Ensure network connectivity to Canvas

### Debug Commands

```bash
# Check server status
sudo systemctl status canvas-mcp-multi-tenant

# View server logs
sudo journalctl -u canvas-mcp-multi-tenant -f

# Test server manually
python deploy/multi-tenant-server.py
```

## File Structure

```
canvas-mcp/
├── deploy/
│   ├── multi-tenant-server.py          # Main server script
│   ├── canvas-mcp-multi-tenant.service # Systemd service file
│   └── INSTALLATION-GUIDE.md          # This guide
├── src/
│   └── canvas_mcp/                    # Original single-tenant server
└── README.md                          # Project documentation
```

## Support

For issues or questions:

1. Check the troubleshooting section above
2. Review server logs: `sudo journalctl -u canvas-mcp-multi-tenant -f`
3. Test the server manually: `python deploy/multi-tenant-server.py`

## License

This project is licensed under the MIT License - see the LICENSE file for details.
