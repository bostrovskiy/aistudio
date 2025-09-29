#!/usr/bin/env python3
"""
Canvas MCP HTTPS Secure Server with Simple Local Credential Storage
This server provides MCP protocol over HTTPS with simple secure credential storage
"""

import asyncio
import json
import sys
import os
import subprocess
import getpass
import base64
import hashlib
from typing import Dict, Any, Optional

class CanvasMCPHTTPSSecureStoredSimpleServer:
    """Secure HTTPS MCP server with simple local credential storage."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.api_token: Optional[str] = None
        self.api_url: Optional[str] = None
        self.institution_name: Optional[str] = None
        self.session_id: Optional[str] = None
        self.authenticated = False
        
        # Try to load stored credentials
        self.load_credentials()
    
    def get_credential_file(self, api_url: str) -> str:
        """Get the path to the credential file for a specific API URL."""
        # Create a hash of the API URL to use as filename
        url_hash = hashlib.sha256(api_url.encode()).hexdigest()[:8]
        home_dir = os.path.expanduser("~")
        return os.path.join(home_dir, f".canvas-mcp-{url_hash}.json")
    
    def store_credentials(self, api_token: str, api_url: str, institution_name: str = ""):
        """Store credentials securely in a local file."""
        try:
            credential_file = self.get_credential_file(api_url)
            
            # Create credentials data
            credentials = {
                "api_token": api_token,
                "api_url": api_url,
                "institution_name": institution_name
            }
            
            # Encode credentials
            encoded_creds = base64.b64encode(json.dumps(credentials).encode()).decode()
            
            # Write to file with restricted permissions
            with open(credential_file, 'w') as f:
                f.write(encoded_creds)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(credential_file, 0o600)
            print("✅ Credentials stored securely", file=sys.stderr)
            
        except Exception as e:
            print(f"⚠️ Could not store credentials: {e}", file=sys.stderr)
    
    def load_credentials(self):
        """Load stored credentials from local file."""
        try:
            # Try to load from environment first (for testing)
            if os.getenv("CANVAS_API_TOKEN") and os.getenv("CANVAS_API_URL"):
                self.api_token = os.getenv("CANVAS_API_TOKEN")
                self.api_url = os.getenv("CANVAS_API_URL")
                self.institution_name = os.getenv("CANVAS_INSTITUTION_NAME", "")
                print("✅ Loaded credentials from environment", file=sys.stderr)
                return
            
            print("ℹ️ No stored credentials found. You'll be prompted to authenticate.", file=sys.stderr)
            
        except Exception as e:
            print(f"ℹ️ Could not load stored credentials: {e}", file=sys.stderr)
    
    def load_credentials_for_url(self, api_url: str):
        """Load credentials for a specific API URL."""
        try:
            credential_file = self.get_credential_file(api_url)
            
            if os.path.exists(credential_file):
                with open(credential_file, 'r') as f:
                    encoded_creds = f.read()
                
                credentials = json.loads(base64.b64decode(encoded_creds).decode())
                self.api_token = credentials["api_token"]
                self.api_url = credentials["api_url"]
                self.institution_name = credentials.get("institution_name", "")
                print("✅ Loaded stored credentials", file=sys.stderr)
                return True
            else:
                print("ℹ️ No stored credentials found for this URL", file=sys.stderr)
                return False
                
        except Exception as e:
            print(f"ℹ️ Could not load stored credentials: {e}", file=sys.stderr)
            return False
    
    def clear_credentials_for_url(self, api_url: str):
        """Clear stored credentials for a specific API URL."""
        try:
            credential_file = self.get_credential_file(api_url)
            if os.path.exists(credential_file):
                os.remove(credential_file)
                print("✅ Stored credentials cleared", file=sys.stderr)
                return True
            else:
                print("ℹ️ No stored credentials found", file=sys.stderr)
                return False
        except Exception as e:
            print(f"⚠️ Could not clear credentials: {e}", file=sys.stderr)
            return False
    
    def make_curl_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request using curl."""
        try:
            url = f"{self.base_url}{endpoint}"
            if params:
                param_str = "&".join([f"{k}={v}" for k, v in params.items()])
                url += f"?{param_str}"
            
            cmd = ["curl", "-s", "-X", method, "-H", "Content-Type: application/json"]
            
            if data:
                cmd.extend(["-d", json.dumps(data)])
            
            cmd.append(url)
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                return {"error": f"curl failed: {result.stderr}"}
            
            return json.loads(result.stdout)
            
        except Exception as e:
            return {"error": str(e)}
    
    def authenticate(self, api_token: str = None, api_url: str = None, institution_name: str = "") -> bool:
        """Authenticate with the Canvas MCP server."""
        try:
            # Use provided credentials or stored ones
            if api_token and api_url:
                self.api_token = api_token
                self.api_url = api_url
                self.institution_name = institution_name
            elif not self.api_token or not self.api_url:
                return False
            
            data = {
                "api_token": self.api_token,
                "api_url": self.api_url,
                "institution_name": self.institution_name
            }
            
            result = self.make_curl_request("POST", "/authenticate", data=data)
            
            if result.get("success"):
                self.session_id = result["session_id"]
                self.authenticated = True
                print(f"✅ Authenticated: {result.get('user_name', 'Unknown')}", file=sys.stderr)
                return True
            else:
                print(f"❌ Authentication failed: {result.get('error', 'Unknown error')}", file=sys.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {e}", file=sys.stderr)
            return False
    
    def make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a request to the Canvas MCP server."""
        if not self.session_id:
            return {"error": "Not authenticated"}
        
        request_params = {"session_id": self.session_id}
        if params:
            request_params.update(params)
        
        return self.make_curl_request("GET", endpoint, params=request_params)
    
    def handle_mcp_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol requests."""
        method = request.get("method", "")
        params = request.get("params", {})
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "canvas-mcp-https-secure-stored",
                        "version": "1.0.0"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "authenticate_canvas",
                            "description": "Authenticate with Canvas credentials (stores securely for future use)",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "api_url": {"type": "string", "description": "Canvas API URL"},
                                    "institution_name": {"type": "string", "description": "Institution name"},
                                    "store_credentials": {"type": "boolean", "description": "Store credentials securely (default: true)"}
                                },
                                "required": ["api_url"]
                            }
                        },
                        {
                            "name": "list_my_courses",
                            "description": "List courses for the authenticated user",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "include_concluded": {"type": "boolean", "description": "Include concluded courses"}
                                }
                            }
                        },
                        {
                            "name": "get_course_details",
                            "description": "Get detailed information about a specific course",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "course_id": {"type": "string", "description": "Canvas course ID"}
                                },
                                "required": ["course_id"]
                            }
                        },
                        {
                            "name": "list_assignments",
                            "description": "List assignments for a specific course",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "course_id": {"type": "string", "description": "Canvas course ID"}
                                },
                                "required": ["course_id"]
                            }
                        },
                        {
                            "name": "get_assignment_details",
                            "description": "Get detailed information about a specific assignment",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "course_id": {"type": "string", "description": "Canvas course ID"},
                                    "assignment_id": {"type": "string", "description": "Canvas assignment ID"}
                                },
                                "required": ["course_id", "assignment_id"]
                            }
                        },
                        {
                            "name": "list_discussions",
                            "description": "List discussions for a specific course",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "course_id": {"type": "string", "description": "Canvas course ID"},
                                    "only_announcements": {"type": "boolean", "description": "Only show announcements"}
                                },
                                "required": ["course_id"]
                            }
                        },
                        {
                            "name": "get_discussion_details",
                            "description": "Get detailed information about a specific discussion",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "course_id": {"type": "string", "description": "Canvas course ID"},
                                    "discussion_id": {"type": "string", "description": "Canvas discussion ID"}
                                },
                                "required": ["course_id", "discussion_id"]
                            }
                        },
                        {
                            "name": "list_announcements",
                            "description": "List announcements for a specific course",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "course_id": {"type": "string", "description": "Canvas course ID"}
                                },
                                "required": ["course_id"]
                            }
                        },
                        {
                            "name": "get_grades",
                            "description": "Get grades for a specific course",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "course_id": {"type": "string", "description": "Canvas course ID"}
                                },
                                "required": ["course_id"]
                            }
                        },
                        {
                            "name": "list_calendar_events",
                            "description": "List calendar events for a specific course",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "course_id": {"type": "string", "description": "Canvas course ID"},
                                    "start_date": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                                    "end_date": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                                },
                                "required": ["course_id"]
                            }
                        },
                        {
                            "name": "search_courses",
                            "description": "Search for courses by name or code",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "search_term": {"type": "string", "description": "Search term"}
                                },
                                "required": ["search_term"]
                            }
                        },
                        {
                            "name": "get_my_profile",
                            "description": "Get Canvas profile information",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "get_session_info",
                            "description": "Get information about your current session",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "logout",
                            "description": "Logout and invalidate your session",
                            "inputSchema": {
                                "type": "object",
                                "properties": {}
                            }
                        },
                        {
                            "name": "clear_stored_credentials",
                            "description": "Clear stored credentials from secure storage",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "api_url": {"type": "string", "description": "Canvas API URL to clear credentials for"}
                                },
                                "required": ["api_url"]
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            
            if tool_name == "authenticate_canvas":
                api_url = params.get("api_url", "")
                institution_name = params.get("institution_name", "")
                store_credentials = params.get("store_credentials", True)
                
                if not api_url:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32602,
                            "message": "API URL is required"
                        }
                    }
                
                # Try to load stored credentials first
                if not self.load_credentials_for_url(api_url):
                    # Prompt for API token securely
                    print("🔐 Please enter your Canvas API token (it will be hidden):", file=sys.stderr)
                    api_token = getpass.getpass("API Token: ")
                else:
                    api_token = self.api_token
                
                success = self.authenticate(api_token, api_url, institution_name)
                if success:
                    # Store credentials if requested
                    if store_credentials:
                        self.store_credentials(api_token, api_url, institution_name)
                    
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"✅ Successfully authenticated with Canvas! Session ID: {self.session_id[:8]}...\n{'🔐 Credentials stored securely for future use.' if store_credentials else '⚠️ Credentials not stored.'}"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32000,
                            "message": "Authentication failed"
                        }
                    }
            
            elif tool_name == "clear_stored_credentials":
                api_url = params.get("api_url", "")
                if not api_url:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32602,
                            "message": "API URL is required"
                        }
                    }
                
                success = self.clear_credentials_for_url(api_url)
                if success:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "✅ Stored credentials cleared successfully"
                                }
                            ]
                        }
                    }
                else:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": "ℹ️ No stored credentials found to clear"
                                }
                            ]
                        }
                    }
            
            elif tool_name == "list_my_courses":
                if not self.authenticated:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32000,
                            "message": "Not authenticated. Please authenticate first."
                        }
                    }
                
                include_concluded = params.get("include_concluded", False)
                result = self.make_request("/courses", {"include_concluded": include_concluded})
                
                if "error" in result:
                    return {
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {
                            "code": -32000,
                            "message": result["error"]
                        }
                    }
                
                courses_text = "📚 **Your Courses:**\n\n"
                for course in result.get("courses", []):
                    courses_text += f"**{course.get('name', 'Unnamed')}**\n"
                    courses_text += f"  - ID: {course.get('id')}\n"
                    courses_text += f"  - Code: {course.get('code', 'N/A')}\n"
                    courses_text += f"  - Term: {course.get('term', 'N/A')}\n"
                    courses_text += f"  - Students: {course.get('students', 0)}\n"
                    courses_text += f"  - Status: {course.get('status', 'Unknown')}\n\n"
                
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": courses_text
                            }
                        ]
                    }
                }
            
            # Add more tool handlers here...
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"Unknown method: {method}"
                }
            }
    
    def run(self):
        """Run the MCP server."""
        # Try to authenticate with stored credentials on startup
        if self.api_token and self.api_url:
            self.authenticate()
        
        # Handle MCP protocol
        while True:
            try:
                line = sys.stdin.readline()
                if not line:
                    break
                
                request = json.loads(line.strip())
                response = self.handle_mcp_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
                
            except Exception as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Canvas MCP HTTPS Secure Server with Stored Credentials")
    parser.add_argument("--base-url", default="https://ai-studio-hw3.ostrovskiy.xyz", help="Base URL for the Canvas MCP server")
    
    args = parser.parse_args()
    
    server = CanvasMCPHTTPSSecureStoredSimpleServer(base_url=args.base_url)
    server.run()

if __name__ == "__main__":
    main()
