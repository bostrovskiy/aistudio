#!/usr/bin/env python3
"""
MCP HTTPS Client for Canvas Server
Connects to the Canvas MCP server via HTTPS using only standard library
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import ssl
from typing import Any, Dict

class MCPHTTPSClient:
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
    
    def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the MCP server"""
        try:
            # Create SSL context that doesn't verify certificates (for development)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Prepare the request data
            data = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or {}
            }
            
            # Encode the data as JSON
            json_data = json.dumps(data).encode('utf-8')
            
            # Create the request
            req = urllib.request.Request(
                f"{self.server_url}/mcp",
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Send the request
            with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32603,
                    "message": f"Connection error: {str(e)}"
                }
            }
    
    def initialize(self):
        """Initialize the MCP connection"""
        result = self.send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {
                    "listChanged": True
                },
                "sampling": {}
            },
            "clientInfo": {
                "name": "claude-desktop",
                "version": "1.0.0"
            }
        })
        return result
    
    def list_tools(self):
        """List available tools"""
        return self.send_request("tools/list")
    
    def call_tool(self, name: str, arguments: Dict[str, Any]):
        """Call a specific tool"""
        return self.send_request("tools/call", {
            "name": name,
            "arguments": arguments
        })

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mcp-https-client.py <server_url>")
        sys.exit(1)
    
    server_url = sys.argv[1]
    client = MCPHTTPSClient(server_url)
    
    try:
        # Initialize connection
        init_result = client.initialize()
        print(json.dumps(init_result, indent=2))
        
        # List tools
        tools_result = client.list_tools()
        print(json.dumps(tools_result, indent=2))
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
