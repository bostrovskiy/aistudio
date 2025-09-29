#!/usr/bin/env python3
"""
MCP Canvas Proxy Server
Acts as a local MCP server that proxies requests to the remote Canvas HTTPS server
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import ssl
import asyncio
from typing import Any, Dict

class CanvasMCPProxy:
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
    
    def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the remote Canvas HTTP server"""
        try:
            # Create SSL context that doesn't verify certificates (for development)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Map MCP methods to HTTP endpoints
            if method == "tools/list":
                endpoint = "/assignments"
                data = {}
            elif method == "tools/call":
                tool_name = params.get("name", "")
                if tool_name == "list_assignments":
                    endpoint = "/assignments"
                    data = {}
                else:
                    endpoint = "/assignments"
                    data = {}
            else:
                endpoint = "/"
                data = {}
            
            # Encode the data as JSON
            json_data = json.dumps(data).encode('utf-8')
            
            # Create the request
            req = urllib.request.Request(
                f"{self.server_url}:8080{endpoint}",
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            
            # Send the request
            with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                response_data = response.read().decode('utf-8')
                return {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": response_data
                            }
                        ]
                    }
                }
                
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32603,
                    "message": f"Connection error: {str(e)}"
                }
            }

async def handle_mcp_request(proxy: CanvasMCPProxy, request: Dict[str, Any]) -> Dict[str, Any]:
    """Handle an MCP request by proxying it to the remote server"""
    method = request.get("method", "")
    params = request.get("params", {})
    
    if method == "initialize":
        # Handle initialization locally
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "canvas-mcp-proxy",
                    "version": "1.0.0"
                }
            }
        }
    elif method == "tools/list":
        # Get tools from remote server
        result = proxy.send_request("tools/list")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "result": result.get("result", {"tools": []})
        }
    elif method == "tools/call":
        # Call tool on remote server
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        result = proxy.send_request("tools/call", {
            "name": tool_name,
            "arguments": tool_args
        })
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "result": result.get("result", {})
        }
    else:
        # Proxy other requests
        result = proxy.send_request(method, params)
        return {
            "jsonrpc": "2.0",
            "id": request.get("id", 1),
            "result": result.get("result", {})
        }

async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mcp-canvas-proxy.py <server_url>")
        sys.exit(1)
    
    server_url = sys.argv[1]
    proxy = CanvasMCPProxy(server_url)
    
    # Read MCP requests from stdin and respond via stdout
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                response = await handle_mcp_request(proxy, request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError:
                continue
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    asyncio.run(main())
