#!/usr/bin/env python3
"""
MCP HTTP Client for Canvas Server
Connects to the Canvas HTTPS server and provides MCP protocol interface
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
import ssl
import os
from typing import Any, Dict

class CanvasMCPClient:
    def __init__(self, server_url: str):
        self.server_url = server_url.rstrip('/')
        self.session_id = None
    
    def send_request(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a request to the Canvas HTTPS server"""
        try:
            # Create SSL context that doesn't verify certificates (for development)
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Handle different MCP methods
            if method == "initialize":
                return {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "canvas-mcp-https",
                            "version": "1.0.0"
                        }
                    }
                }
            elif method == "tools/list":
                # Return available tools
                return {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "tools": [
                            {
                                "name": "authenticate_canvas",
                                "description": "Authenticate with Canvas using your API credentials. SECURITY: Token is encrypted in memory and never stored on disk.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "api_token": {"type": "string", "description": "Your Canvas API token"},
                                        "api_url": {"type": "string", "description": "Your Canvas API URL (e.g., https://your-school.canvas.edu/api/v1)"},
                                        "institution_name": {"type": "string", "description": "Your institution name (optional)"}
                                    },
                                    "required": ["api_token", "api_url"]
                                }
                            },
                            {
                                "name": "logout",
                                "description": "Securely logout and clear all authentication data from memory",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "list_courses",
                                "description": "List all your courses",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "include_concluded": {"type": "boolean", "description": "Include concluded courses", "default": False}
                                    }
                                }
                            },
                            {
                                "name": "list_assignments",
                                "description": "List assignments for a course",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "course_id": {"type": "string", "description": "Course ID"}
                                    },
                                    "required": ["course_id"]
                                }
                            },
                            {
                                "name": "get_assignments_due_tomorrow",
                                "description": "Get assignments due tomorrow",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            }
                        ]
                    }
                }
            elif method == "tools/call":
                tool_name = params.get("name", "")
                tool_args = params.get("arguments", {})
                
                # Handle authentication
                if tool_name == "authenticate_canvas":
                    # Use provided arguments (Claude will ask user for these)
                    api_token = tool_args.get("api_token", "")
                    api_url = tool_args.get("api_url", "")
                    institution_name = tool_args.get("institution_name", "")
                    
                    if not api_token or not api_url:
                        return {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "error": {
                                "code": -32602,
                                "message": "Please provide your Canvas API token and API URL. Use the authenticate_canvas tool first."
                            }
                        }
                    
                    # Make POST request to authenticate
                    auth_data = {
                        "api_token": api_token,
                        "api_url": api_url,
                        "institution_name": institution_name
                    }
                    
                    url = f"{self.server_url}/authenticate"
                    req = urllib.request.Request(url, 
                                                data=json.dumps(auth_data).encode('utf-8'),
                                                headers={'Content-Type': 'application/json'})
                    
                    with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                        response_data = response.read().decode('utf-8')
                        auth_response = json.loads(response_data)
                        
                        # Store session ID for future requests
                        if 'session_id' in auth_response:
                            self.session_id = auth_response['session_id']
                        
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
                
                # Handle other tools
                elif tool_name in ["logout", "list_courses", "list_assignments", "get_assignments_due_tomorrow"]:
                    # Check if authenticated
                    if not self.session_id and tool_name != "logout":
                        return {
                            "jsonrpc": "2.0",
                            "id": 1,
                            "error": {
                                "code": -32602,
                                "message": "Please authenticate first using authenticate_canvas."
                            }
                        }
                    
                    # Build endpoint based on tool
                    if tool_name == "logout":
                        endpoint = f"/logout?session_id={self.session_id}" if self.session_id else "/logout"
                    elif tool_name == "list_courses":
                        include_concluded = tool_args.get("include_concluded", False)
                        endpoint = f"/courses?session_id={self.session_id}&include_concluded={include_concluded}"
                    elif tool_name == "list_assignments":
                        course_id = tool_args.get("course_id", "")
                        endpoint = f"/assignments?session_id={self.session_id}&course_id={course_id}"
                    elif tool_name == "get_assignments_due_tomorrow":
                        endpoint = f"/assignments_due_tomorrow?session_id={self.session_id}"
                    else:
                        endpoint = "/"
                    
                    # Make HTTP request to the server
                    url = f"{self.server_url}{endpoint}"
                    req = urllib.request.Request(url)
                    
                    with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
                        response_data = response.read().decode('utf-8')
                        
                        # Clear session on logout
                        if tool_name == "logout":
                            self.session_id = None
                        
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
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        }
                    }
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
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

def main():
    # Get server URL from environment variable or command line
    server_url = os.getenv('SERVER_URL')
    if not server_url:
        if len(sys.argv) < 2:
            print("Usage: python3 mcp-http-client.py <server_url>")
            print("Or set SERVER_URL environment variable")
            sys.exit(1)
        server_url = sys.argv[1]
    
    client = CanvasMCPClient(server_url)
    
    # Read MCP requests from stdin and respond via stdout
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            
            try:
                request = json.loads(line.strip())
                method = request.get("method", "")
                params = request.get("params", {})
                
                response = client.send_request(method, params)
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
    main()
