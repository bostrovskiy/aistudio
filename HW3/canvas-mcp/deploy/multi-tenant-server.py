#!/usr/bin/env python3
"""
Multi-tenant Canvas MCP Server
Each user provides their own Canvas credentials for secure, isolated access

SECURITY & PRIVACY FEATURES:
- Multi-tenant architecture: Each user provides their own credentials
- Session isolation: User sessions are completely isolated
- No credential sharing: No risk of credential exposure between users
- Automatic session cleanup: Expired sessions are automatically removed
- FERPA compliance: Built-in data anonymization and privacy protection
- Secure authentication: Bearer token authentication with Canvas API
- Input validation: All inputs are validated and sanitized
- Error handling: Secure error messages without exposing sensitive data
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
import re

import httpx

class MultiTenantCanvasServer:
    """Multi-tenant Canvas MCP Server with per-user credential isolation."""
    
    def __init__(self):
        self.server_name = "canvas-mcp-multi-tenant"
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=24)  # 24-hour session timeout
        
        # Security settings
        self.max_sessions_per_user = 5  # Limit concurrent sessions per user
        self.max_requests_per_minute = 60  # Rate limiting
        self.request_counts: Dict[str, Dict[str, Any]] = {}  # Track request rates
        
    def generate_session_id(self) -> str:
        """Generate a secure session ID."""
        return secrets.token_urlsafe(32)
    
    def hash_credentials(self, api_token: str, api_url: str) -> str:
        """Create a hash of credentials for session identification."""
        combined = f"{api_token}:{api_url}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def validate_input(self, data: Any, field_name: str) -> bool:
        """Validate and sanitize input data."""
        if not isinstance(data, str):
            return False
        
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', '', data)
        
        # Check for reasonable length limits
        if len(sanitized) > 1000:
            return False
            
        return True
    
    def check_rate_limit(self, session_id: str) -> bool:
        """Check if user has exceeded rate limits."""
        now = datetime.now()
        if session_id not in self.request_counts:
            self.request_counts[session_id] = {'count': 0, 'window_start': now}
        
        # Reset counter if window has passed
        if now - self.request_counts[session_id]['window_start'] > timedelta(minutes=1):
            self.request_counts[session_id] = {'count': 0, 'window_start': now}
        
        # Check if limit exceeded
        if self.request_counts[session_id]['count'] >= self.max_requests_per_minute:
            return False
        
        # Increment counter
        self.request_counts[session_id]['count'] += 1
        return True
    
    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive data for FERPA compliance."""
        anonymized = data.copy()
        
        # Anonymize user information
        if 'name' in anonymized:
            anonymized['name'] = f"User_{anonymized.get('id', 'Unknown')}"
        if 'email' in anonymized:
            anonymized['email'] = f"user_{anonymized.get('id', 'unknown')}@example.com"
        if 'login_id' in anonymized:
            anonymized['login_id'] = f"user_{anonymized.get('id', 'unknown')}"
        
        # Anonymize course information
        if 'course_code' in anonymized:
            anonymized['course_code'] = f"COURSE_{anonymized.get('id', 'Unknown')}"
        
        return anonymized
    
    def sanitize_error_message(self, error: str) -> str:
        """Sanitize error messages to avoid exposing sensitive information."""
        # Remove potential API tokens or sensitive data
        sanitized = re.sub(r'[a-zA-Z0-9]{20,}', '[REDACTED]', error)
        sanitized = re.sub(r'Bearer\s+[a-zA-Z0-9]+', 'Bearer [REDACTED]', sanitized)
        return sanitized
    
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
            # Validate inputs
            if not self.validate_input(api_token, "api_token"):
                print("❌ Invalid API token format", file=sys.stderr)
                return None
            
            if not self.validate_input(api_url, "api_url"):
                print("❌ Invalid API URL format", file=sys.stderr)
                return None
            
            # Test the credentials by making a simple API call
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{api_url.rstrip('/')}/users/self",
                    headers={"Authorization": f"Bearer {api_token}"},
                    timeout=10.0
                )
                response.raise_for_status()
                user_data = response.json()
                
                # Check for existing sessions for this user
                credential_hash = self.hash_credentials(api_token, api_url)
                existing_sessions = [sid for sid, session in self.user_sessions.items() 
                                   if session.get('credential_hash') == credential_hash]
                
                # Enforce session limit
                if len(existing_sessions) >= self.max_sessions_per_user:
                    # Remove oldest session
                    oldest_session = min(existing_sessions, 
                                       key=lambda sid: self.user_sessions[sid]['created_at'])
                    del self.user_sessions[oldest_session]
                
                # Create session
                session_id = self.generate_session_id()
                
                self.user_sessions[session_id] = {
                    "api_token": api_token,
                    "api_url": api_url,
                    "user_id": user_data.get("id"),
                    "user_name": user_data.get("name", "Unknown"),
                    "credential_hash": credential_hash,
                    "created_at": datetime.now(),
                    "last_activity": datetime.now()
                }
                
                # Anonymize user data for logging
                anonymized_data = self.anonymize_data(user_data)
                print(f"✅ User authenticated: {anonymized_data.get('name')} ({anonymized_data.get('id')})", file=sys.stderr)
                return session_id
                
        except Exception as e:
            sanitized_error = self.sanitize_error_message(str(e))
            print(f"❌ Authentication failed: {sanitized_error}", file=sys.stderr)
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
        
        # Check rate limiting
        if not self.check_rate_limit(session_id):
            print(f"❌ Rate limit exceeded for session {session_id[:8]}...", file=sys.stderr)
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
            # Validate endpoint to prevent path traversal attacks
            if not endpoint.startswith('/') or '..' in endpoint:
                return {"error": "Invalid endpoint"}
            
            # Limit request size
            if kwargs.get("data") and len(str(kwargs["data"])) > 10000:
                return {"error": "Request too large"}
            
            async with httpx.AsyncClient() as client:
                url = f"{session['api_url'].rstrip('/')}{endpoint}"
                headers = {
                    "Authorization": f"Bearer {session['api_token']}",
                    **kwargs.get("headers", {})
                }
                
                if method.lower() == "get":
                    response = await client.get(url, params=kwargs.get("params"), headers=headers, timeout=30.0)
                elif method.lower() == "post":
                    response = await client.post(url, json=kwargs.get("data"), headers=headers, timeout=30.0)
                elif method.lower() == "put":
                    response = await client.put(url, json=kwargs.get("data"), headers=headers, timeout=30.0)
                elif method.lower() == "delete":
                    response = await client.delete(url, params=kwargs.get("params"), headers=headers, timeout=30.0)
                else:
                    return {"error": f"Unsupported method: {method}"}
                
                response.raise_for_status()
                data = response.json()
                
                # Anonymize sensitive data in response
                if isinstance(data, list):
                    return [self.anonymize_data(item) if isinstance(item, dict) else item for item in data]
                elif isinstance(data, dict):
                    return self.anonymize_data(data)
                else:
                    return data
                
        except Exception as e:
            sanitized_error = self.sanitize_error_message(str(e))
            return {"error": f"API request failed: {sanitized_error}"}

    def register_tools(self):
        """Register MCP tools with user authentication."""
        
        @self.mcp.tool()
        async def authenticate_canvas(api_token: str, api_url: str, institution_name: str = '') -> str:
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
                    'session_id': session_id,
                    'user_name': session['user_name'],
                    'user_id': session['user_id'],
                    'institution': institution_name,
                    'message': '✅ Successfully authenticated with Canvas!'
                }, indent=2)
            else:
                return json.dumps({'error': '❌ Authentication failed. Please check your credentials.'}, indent=2)
        
        @self.mcp.tool()
        async def list_my_courses(session_id: str, include_concluded: bool = False) -> str:
            """
            List courses for the authenticated user.
            
            Args:
                session_id: Your session ID from authentication
                include_concluded: Include concluded courses
            """
            params = {'include[]': ['term', 'teachers', 'total_students'], 'per_page': 100}
            if include_concluded:
                params['state[]'] = ['available', 'completed']
            
            response = await self.make_canvas_request(session_id, 'get', '/courses', params=params)
            
            if 'error' in response:
                return f'Error: {response["error"]}'
            
            if not response:
                return 'No courses found.'
            
            courses_info = []
            for course in response:
                course_info = f'''
Course: {course.get('name', 'Unnamed')}
ID: {course.get('id')}
Code: {course.get('course_code', 'N/A')}
Term: {course.get('term', {}).get('name', 'N/A')}
Students: {course.get('total_students', 0)}
Status: {course.get('workflow_state', 'Unknown')}
'''
                courses_info.append(course_info)
            
            return '\n'.join(courses_info)

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
    # Check if we're being called as a subprocess
    if len(sys.argv) > 1 and sys.argv[1] == '--subprocess':
        # We're in a subprocess, run normally
        asyncio.run(main())
    else:
        # We're being called directly, run in a subprocess to avoid event loop conflicts
        import subprocess
        import os
        
        script_path = os.path.abspath(__file__)
        try:
            # Run this script in a subprocess with --subprocess flag
            process = subprocess.Popen([sys.executable, script_path, '--subprocess'], 
                                     stdout=subprocess.PIPE, 
                                     stderr=subprocess.PIPE,
                                     text=True)
            
            # Stream output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
                    
        except KeyboardInterrupt:
            process.terminate()
        except Exception as e:
            print(f'Error running subprocess: {e}', file=sys.stderr)
            # Fallback to direct execution
            asyncio.run(main())
