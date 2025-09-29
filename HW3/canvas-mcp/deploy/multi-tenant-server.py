#!/usr/bin/env python3
"""
Multi-tenant Canvas MCP Server
Each user provides their own Canvas credentials for secure, isolated access
"""

import asyncio
import json
import os
import sys
import time
import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
import secrets

from mcp.server.fastmcp import FastMCP
from mcp.server.models import InitializationOptions
import httpx

# Fix asyncio event loop issue
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
else:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new one
            asyncio.set_event_loop(asyncio.new_event_loop())
    except RuntimeError:
        # No event loop exists, create one
        asyncio.set_event_loop(asyncio.new_event_loop())

class MultiTenantCanvasServer:
    """Multi-tenant Canvas MCP Server with per-user credential isolation."""
    
    def __init__(self):
        self.server_name = "canvas-mcp-multi-tenant"
        self.mcp = FastMCP(self.server_name)
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=24)  # 24-hour session timeout
        
    def generate_session_id(self) -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)
    
    def hash_credentials(self, api_token: str, api_url: str) -> str:
        """Create a hash of credentials for session identification."""
        combined = f"{api_token}:{api_url}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    async def authenticate_user(self, api_token: str, api_url: str) -> Optional[str]:
        """
        Authenticate a user with their Canvas credentials.
        
        Args:
            api_token: User's Canvas API token
            api_url: User's Canvas API URL
            
        Returns:
            session_id if authentication successful, None otherwise
        """
        try:
            # Test the credentials by making a simple API call
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{api_url.rstrip('/')}/users/self",
                    headers={"Authorization": f"Bearer {api_token}"},
                    timeout=10.0
                )
                response.raise_for_status()
                user_data = response.json()
                
                # Create session
                session_id = self.generate_session_id()
                credential_hash = self.hash_credentials(api_token, api_url)
                
                self.user_sessions[session_id] = {
                    "api_token": api_token,
                    "api_url": api_url,
                    "user_id": user_data.get("id"),
                    "user_name": user_data.get("name", "Unknown"),
                    "credential_hash": credential_hash,
                    "created_at": datetime.now(),
                    "last_activity": datetime.now()
                }
                
                print(f"✅ User authenticated: {user_data.get('name')} ({user_data.get('id')})", file=sys.stderr)
                return session_id
                
        except Exception as e:
            print(f"❌ Authentication failed: {e}", file=sys.stderr)
            return None
    
    def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get user session if valid and not expired."""
        if session_id not in self.user_sessions:
            return None
            
        session = self.user_sessions[session_id]
        
        # Check if session is expired
        if datetime.now() - session["last_activity"] > self.session_timeout:
            del self.user_sessions[session_id]
            return None
            
        # Update last activity
        session["last_activity"] = datetime.now()
        return session
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, session in self.user_sessions.items()
            if now - session["last_activity"] > self.session_timeout
        ]
        
        for session_id in expired_sessions:
            del self.user_sessions[session_id]
    
    async def make_canvas_request(self, session_id: str, method: str, endpoint: str, **kwargs) -> Any:
        """Make a Canvas API request using the user's credentials."""
        session = self.get_user_session(session_id)
        if not session:
            return {"error": "Invalid or expired session. Please re-authenticate."}
        
        try:
            async with httpx.AsyncClient() as client:
                url = f"{session['api_url'].rstrip('/')}{endpoint}"
                headers = {
                    "Authorization": f"Bearer {session['api_token']}",
                    **kwargs.get("headers", {})
                }
                
                if method.lower() == "get":
                    response = await client.get(url, params=kwargs.get("params"), headers=headers)
                elif method.lower() == "post":
                    response = await client.post(url, json=kwargs.get("data"), headers=headers)
                elif method.lower() == "put":
                    response = await client.put(url, json=kwargs.get("data"), headers=headers)
                elif method.lower() == "delete":
                    response = await client.delete(url, params=kwargs.get("params"), headers=headers)
                else:
                    return {"error": f"Unsupported method: {method}"}
                
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            return {"error": f"API request failed: {str(e)}"}

    def register_tools(self):
        """Register MCP tools with user authentication."""
        
        @self.mcp.tool()
        async def authenticate_canvas(
            api_token: str,
            api_url: str,
            institution_name: str = ""
        ) -> str:
            """
            Authenticate with your Canvas credentials.
            
            Args:
                api_token: Your Canvas API token (get from Canvas → Account → Settings → New Access Token)
                api_url: Your Canvas API URL (e.g., https://your-school.canvas.edu/api/v1)
                institution_name: Your institution name (optional)
            
            Returns:
                Session ID for authenticated requests
            """
            session_id = await self.authenticate_user(api_token, api_url)
            if session_id:
                session = self.user_sessions[session_id]
                return json.dumps({
                    "session_id": session_id,
                    "user_name": session["user_name"],
                    "user_id": session["user_id"],
                    "institution": institution_name,
                    "message": "✅ Successfully authenticated with Canvas!"
                }, indent=2)
            else:
                return json.dumps({
                    "error": "❌ Authentication failed. Please check your credentials."
                }, indent=2)
        
        @self.mcp.tool()
        async def list_my_courses(session_id: str, include_concluded: bool = False) -> str:
            """
            List courses for the authenticated user.
            
            Args:
                session_id: Your session ID from authentication
                include_concluded: Include concluded courses
            """
            params = {
                "include[]": ["term", "teachers", "total_students"],
                "per_page": 100
            }
            if include_concluded:
                params["state[]"] = ["available", "completed"]
            
            response = await self.make_canvas_request(session_id, "get", "/courses", params=params)
            
            if "error" in response:
                return f"Error: {response['error']}"
            
            if not response:
                return "No courses found."
            
            courses_info = []
            for course in response:
                course_info = f"""
Course: {course.get('name', 'Unnamed')}
ID: {course.get('id')}
Code: {course.get('course_code', 'N/A')}
Term: {course.get('term', {}).get('name', 'N/A')}
Students: {course.get('total_students', 0)}
Status: {course.get('workflow_state', 'Unknown')}
"""
                courses_info.append(course_info)
            
            return "\n".join(courses_info)
        
        @self.mcp.tool()
        async def get_my_profile(session_id: str) -> str:
            """
            Get your Canvas profile information.
            
            Args:
                session_id: Your session ID from authentication
            """
            response = await self.make_canvas_request(session_id, "get", "/users/self")
            
            if "error" in response:
                return f"Error: {response['error']}"
            
            profile = f"""
Name: {response.get('name', 'N/A')}
Email: {response.get('email', 'N/A')}
ID: {response.get('id', 'N/A')}
Login ID: {response.get('login_id', 'N/A')}
Created: {response.get('created_at', 'N/A')}
"""
            return profile
        
        @self.mcp.tool()
        async def list_my_assignments(session_id: str, course_id: str) -> str:
            """
            List assignments for a specific course.
            
            Args:
                session_id: Your session ID from authentication
                course_id: Canvas course ID
            """
            params = {
                "per_page": 100,
                "include[]": ["all_dates", "submission"]
            }
            
            response = await self.make_canvas_request(
                session_id, "get", f"/courses/{course_id}/assignments", params=params
            )
            
            if "error" in response:
                return f"Error: {response['error']}"
            
            if not response:
                return f"No assignments found for course {course_id}."
            
            assignments_info = []
            for assignment in response:
                assignment_info = f"""
Assignment: {assignment.get('name', 'Unnamed')}
ID: {assignment.get('id')}
Due: {assignment.get('due_at', 'No due date')}
Points: {assignment.get('points_possible', 0)}
Status: {assignment.get('submission', {}).get('workflow_state', 'Not submitted')}
"""
                assignments_info.append(assignment_info)
            
            return "\n".join(assignments_info)
        
        @self.mcp.tool()
        async def get_session_info(session_id: str) -> str:
            """
            Get information about your current session.
            
            Args:
                session_id: Your session ID from authentication
            """
            session = self.get_user_session(session_id)
            if not session:
                return "❌ Invalid or expired session. Please re-authenticate."
            
            info = f"""
Session ID: {session_id}
User: {session['user_name']} (ID: {session['user_id']})
Canvas URL: {session['api_url']}
Created: {session['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
Last Activity: {session['last_activity'].strftime('%Y-%m-%d %H:%M:%S')}
"""
            return info
        
        @self.mcp.tool()
        async def logout(session_id: str) -> str:
            """
            Logout and invalidate your session.
            
            Args:
                session_id: Your session ID from authentication
            """
            if session_id in self.user_sessions:
                user_name = self.user_sessions[session_id]["user_name"]
                del self.user_sessions[session_id]
                return f"✅ Successfully logged out {user_name}"
            else:
                return "❌ Session not found or already expired"
        
        @self.mcp.tool()
        async def cleanup_sessions() -> str:
            """Clean up expired sessions (admin function)."""
            before_count = len(self.user_sessions)
            self.cleanup_expired_sessions()
            after_count = len(self.user_sessions)
            cleaned = before_count - after_count
            
            return f"✅ Cleaned up {cleaned} expired sessions. Active sessions: {after_count}"

    async def run(self):
        """Run the multi-tenant MCP server."""
        print(f"🚀 Starting Multi-Tenant Canvas MCP Server...", file=sys.stderr)
        print(f"🔐 Each user must authenticate with their own Canvas credentials", file=sys.stderr)
        print(f"⏰ Session timeout: {self.session_timeout}", file=sys.stderr)
        
        self.register_tools()
        
        try:
            await self.mcp.run()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped", file=sys.stderr)
        except Exception as e:
            print(f"❌ Server error: {e}", file=sys.stderr)
            sys.exit(1)

async def main():
    """Main entry point."""
    server = MultiTenantCanvasServer()
    await server.run()

if __name__ == "__main__":
    # Additional asyncio fix for systemd service
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    
    # Run the server
    asyncio.run(main())
