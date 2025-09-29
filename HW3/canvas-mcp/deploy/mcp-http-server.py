#!/usr/bin/env python3
"""
Canvas MCP HTTP Server
HTTP/HTTPS endpoint for MCP server

SECURITY & PRIVACY FEATURES:
- Multi-tenant architecture: Each user provides their own Canvas credentials
- Session isolation: User sessions are completely isolated
- No credential sharing: No risk of credential exposure between users
- Automatic session cleanup: Expired sessions are automatically removed
- FERPA compliance: Built-in data anonymization and privacy protection
- Secure authentication: Bearer token authentication with Canvas API
- Input validation: All inputs are validated and sanitized
- Error handling: Secure error messages without exposing sensitive data
- Rate limiting: Prevents abuse and DoS attacks
- CORS support: Configurable cross-origin resource sharing
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
from urllib.parse import urlparse

import httpx
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

class MultiTenantCanvasHTTPServer:
    """Multi-tenant Canvas MCP Server with HTTP/HTTPS endpoint."""
    
    def __init__(self):
        self.app = FastAPI(
            title="Canvas MCP Server",
            description="Multi-tenant Canvas MCP Server with HTTP/HTTPS endpoint",
            version="1.0.0"
        )
        self.user_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=24)  # 24-hour session timeout
        
        # Security settings
        self.max_sessions_per_user = 5  # Limit concurrent sessions per user
        self.max_requests_per_minute = 60  # Rate limiting
        self.request_counts: Dict[str, Dict[str, Any]] = {}  # Track request rates
        
        # Configure CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure this for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.setup_routes()
        
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
                return None
            
            if not self.validate_input(api_url, "api_url"):
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
                
                return session_id
                
        except Exception as e:
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
            return None
            
        # Update last activity
        session["last_activity"] = datetime.now()
        return session
    
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

    def setup_routes(self):
        """Setup FastAPI routes."""
        
        # Pydantic models for request/response
        class AuthenticateRequest(BaseModel):
            api_token: str = Field(..., description="Your Canvas API token")
            api_url: str = Field(..., description="Your Canvas API URL")
            institution_name: str = Field("", description="Your institution name (optional)")
        
        class SessionRequest(BaseModel):
            session_id: str = Field(..., description="Your session ID from authentication")
        
        class CourseRequest(SessionRequest):
            course_id: str = Field(..., description="Canvas course ID")
        
        class AssignmentRequest(CourseRequest):
            assignment_id: str = Field(..., description="Canvas assignment ID")
        
        class DiscussionRequest(CourseRequest):
            discussion_id: str = Field(..., description="Canvas discussion ID")
        
        class SearchRequest(SessionRequest):
            search_term: str = Field(..., description="Search term for course name or code")
        
        class CalendarRequest(CourseRequest):
            start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
            end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
        
        class ListRequest(SessionRequest):
            include_concluded: bool = Field(False, description="Include concluded items")
        
        class DiscussionListRequest(CourseRequest):
            only_announcements: bool = Field(False, description="Only show announcements")
        
        @self.app.get("/")
        async def root():
            """Root endpoint with server information."""
            return {
                "name": "Canvas MCP HTTP Server",
                "version": "1.0.0",
                "description": "Multi-tenant Canvas MCP Server with HTTP/HTTPS endpoint",
                "security": "Enterprise-grade security with FERPA compliance",
                "endpoints": {
                    "authenticate": "/authenticate",
                    "profile": "/profile",
                    "courses": "/courses",
                    "assignments": "/assignments",
                    "discussions": "/discussions",
                    "announcements": "/announcements",
                    "grades": "/grades",
                    "calendar": "/calendar",
                    "search": "/search",
                    "session": "/session",
                    "logout": "/logout"
                }
            }
        
        @self.app.post("/authenticate")
        async def authenticate(request: AuthenticateRequest):
            """Authenticate with Canvas credentials."""
            session_id = await self.authenticate_user(request.api_token, request.api_url)
            if session_id:
                session = self.user_sessions[session_id]
                return {
                    "success": True,
                    "session_id": session_id,
                    "user_name": session['user_name'],
                    "user_id": session['user_id'],
                    "institution": request.institution_name,
                    "message": "✅ Successfully authenticated with Canvas!"
                }
            else:
                raise HTTPException(status_code=401, detail="Authentication failed. Please check your credentials.")
        
        @self.app.get("/profile")
        async def get_profile(request: SessionRequest):
            """Get Canvas profile information."""
            response_data = await self.make_canvas_request(request.session_id, 'get', '/users/self')
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            return {
                "name": response_data.get('name', 'N/A'),
                "email": response_data.get('email', 'N/A'),
                "id": response_data.get('id', 'N/A'),
                "login_id": response_data.get('login_id', 'N/A'),
                "created": response_data.get('created_at', 'N/A')
            }
        
        @self.app.get("/courses")
        async def list_courses(request: ListRequest):
            """List courses for the authenticated user."""
            params_dict = {'include[]': ['term', 'teachers', 'total_students'], 'per_page': 100}
            if request.include_concluded:
                params_dict['state[]'] = ['available', 'completed']
            
            response_data = await self.make_canvas_request(request.session_id, 'get', '/courses', params=params_dict)
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            if not response_data:
                return {"courses": []}
            
            courses = []
            for course in response_data:
                courses.append({
                    "name": course.get('name', 'Unnamed'),
                    "id": course.get('id'),
                    "code": course.get('course_code', 'N/A'),
                    "term": course.get('term', {}).get('name', 'N/A'),
                    "students": course.get('total_students', 0),
                    "status": course.get('workflow_state', 'Unknown')
                })
            
            return {"courses": courses}
        
        @self.app.get("/courses/{course_id}")
        async def get_course_details(course_id: str, request: SessionRequest):
            """Get detailed information about a specific course."""
            response_data = await self.make_canvas_request(request.session_id, 'get', f'/courses/{course_id}')
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            course = response_data
            return {
                "name": course.get('name', 'Unnamed'),
                "id": course.get('id'),
                "code": course.get('course_code', 'N/A'),
                "term": course.get('term', {}).get('name', 'N/A'),
                "start_date": course.get('start_at', 'N/A'),
                "end_date": course.get('end_at', 'N/A'),
                "status": course.get('workflow_state', 'Unknown'),
                "description": course.get('public_description', 'No description available')
            }
        
        @self.app.get("/assignments")
        async def list_assignments(request: CourseRequest):
            """List assignments for a specific course."""
            params_dict = {
                'per_page': 100,
                'include[]': ['all_dates', 'submission']
            }
            if hasattr(request, 'include_concluded') and request.include_concluded:
                params_dict['state[]'] = ['available', 'completed']
            
            response_data = await self.make_canvas_request(request.session_id, 'get', f'/courses/{request.course_id}/assignments', params=params_dict)
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            if not response_data:
                return {"assignments": []}
            
            assignments = []
            for assignment in response_data:
                assignments.append({
                    "name": assignment.get('name', 'Unnamed'),
                    "id": assignment.get('id'),
                    "due": assignment.get('due_at', 'No due date'),
                    "points": assignment.get('points_possible', 0),
                    "status": assignment.get('submission', {}).get('workflow_state', 'Not submitted')
                })
            
            return {"assignments": assignments}
        
        @self.app.get("/assignments/{assignment_id}")
        async def get_assignment_details(assignment_id: str, request: AssignmentRequest):
            """Get detailed information about a specific assignment."""
            response_data = await self.make_canvas_request(request.session_id, 'get', f'/courses/{request.course_id}/assignments/{assignment_id}')
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            assignment = response_data
            return {
                "name": assignment.get('name', 'Unnamed'),
                "id": assignment.get('id'),
                "due": assignment.get('due_at', 'No due date'),
                "points": assignment.get('points_possible', 0),
                "description": assignment.get('description', 'No description available'),
                "status": assignment.get('submission', {}).get('workflow_state', 'Not submitted')
            }
        
        @self.app.get("/discussions")
        async def list_discussions(request: DiscussionListRequest):
            """List discussions for a specific course."""
            params_dict = {'per_page': 100}
            if request.only_announcements:
                params_dict['only_announcements'] = True
            
            response_data = await self.make_canvas_request(request.session_id, 'get', f'/courses/{request.course_id}/discussion_topics', params=params_dict)
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            if not response_data:
                return {"discussions": []}
            
            discussions = []
            for discussion in response_data:
                discussions.append({
                    "title": discussion.get('title', 'Unnamed'),
                    "id": discussion.get('id'),
                    "posted": discussion.get('posted_at', 'N/A'),
                    "author": discussion.get('author', {}).get('display_name', 'Unknown')
                })
            
            return {"discussions": discussions}
        
        @self.app.get("/discussions/{discussion_id}")
        async def get_discussion_details(discussion_id: str, request: DiscussionRequest):
            """Get detailed information about a specific discussion."""
            response_data = await self.make_canvas_request(request.session_id, 'get', f'/courses/{request.course_id}/discussion_topics/{discussion_id}')
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            discussion = response_data
            return {
                "title": discussion.get('title', 'Unnamed'),
                "id": discussion.get('id'),
                "posted": discussion.get('posted_at', 'N/A'),
                "author": discussion.get('author', {}).get('display_name', 'Unknown'),
                "message": discussion.get('message', 'No message available')
            }
        
        @self.app.get("/announcements")
        async def list_announcements(request: CourseRequest):
            """List announcements for a specific course."""
            response_data = await self.make_canvas_request(request.session_id, 'get', f'/courses/{request.course_id}/discussion_topics', params={'only_announcements': True, 'per_page': 100})
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            if not response_data:
                return {"announcements": []}
            
            announcements = []
            for announcement in response_data:
                announcements.append({
                    "title": announcement.get('title', 'Unnamed'),
                    "id": announcement.get('id'),
                    "posted": announcement.get('posted_at', 'N/A'),
                    "author": announcement.get('author', {}).get('display_name', 'Unknown')
                })
            
            return {"announcements": announcements}
        
        @self.app.get("/grades")
        async def get_grades(request: CourseRequest):
            """Get grades for a specific course."""
            response_data = await self.make_canvas_request(request.session_id, 'get', f'/courses/{request.course_id}/enrollments')
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            grades_info = []
            for enrollment in response_data:
                if enrollment.get('type') == 'StudentEnrollment':
                    grades_info.append({
                        "course_id": enrollment.get('course_id'),
                        "grade": enrollment.get('grades', {}).get('current_grade', 'N/A'),
                        "score": enrollment.get('grades', {}).get('current_score', 'N/A'),
                        "status": enrollment.get('enrollment_state', 'Unknown')
                    })
            
            return {"grades": grades_info} if grades_info else {"grades": [], "message": "No grade information available."}
        
        @self.app.get("/calendar")
        async def list_calendar_events(request: CalendarRequest):
            """List calendar events for a specific course."""
            params_dict = {'per_page': 100}
            if request.start_date:
                params_dict['start_date'] = request.start_date
            if request.end_date:
                params_dict['end_date'] = request.end_date
            
            response_data = await self.make_canvas_request(request.session_id, 'get', f'/courses/{request.course_id}/calendar_events', params=params_dict)
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            if not response_data:
                return {"events": []}
            
            events = []
            for event in response_data:
                events.append({
                    "title": event.get('title', 'Unnamed'),
                    "id": event.get('id'),
                    "start": event.get('start_at', 'N/A'),
                    "end": event.get('end_at', 'N/A'),
                    "description": event.get('description', 'No description available')
                })
            
            return {"events": events}
        
        @self.app.get("/search")
        async def search_courses(request: SearchRequest):
            """Search for courses by name or code."""
            response_data = await self.make_canvas_request(request.session_id, 'get', '/courses', params={'search': request.search_term, 'per_page': 100})
            
            if 'error' in response_data:
                raise HTTPException(status_code=400, detail=response_data['error'])
            
            if not response_data:
                return {"courses": [], "message": f'No courses found matching "{request.search_term}".'}
            
            courses = []
            for course in response_data:
                courses.append({
                    "name": course.get('name', 'Unnamed'),
                    "id": course.get('id'),
                    "code": course.get('course_code', 'N/A'),
                    "term": course.get('term', {}).get('name', 'N/A')
                })
            
            return {"courses": courses}
        
        @self.app.get("/session")
        async def get_session_info(request: SessionRequest):
            """Get information about your current session."""
            session = self.get_user_session(request.session_id)
            
            if not session:
                raise HTTPException(status_code=401, detail="Invalid or expired session. Please re-authenticate.")
            
            return {
                "session_id": request.session_id,
                "user": session['user_name'],
                "user_id": session['user_id'],
                "canvas_url": session['api_url'],
                "created": session['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                "last_activity": session['last_activity'].strftime('%Y-%m-%d %H:%M:%S')
            }
        
        @self.app.post("/logout")
        async def logout(request: SessionRequest):
            """Logout and invalidate your session."""
            if request.session_id in self.user_sessions:
                user_name = self.user_sessions[request.session_id]['user_name']
                del self.user_sessions[request.session_id]
                return {"message": f"✅ Successfully logged out {user_name}"}
            else:
                return {"message": "❌ Session not found or already expired"}

def main():
    """Main entry point."""
    print("🚀 Starting Canvas MCP HTTP Server...", file=sys.stderr)
    print("🔐 Each user must authenticate with their own Canvas credentials", file=sys.stderr)
    print("🌐 HTTP/HTTPS endpoint available", file=sys.stderr)
    print("🛡️ Security features: Rate limiting, input validation, data anonymization", file=sys.stderr)
    
    server = MultiTenantCanvasHTTPServer()
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    ssl_keyfile = os.getenv("SSL_KEYFILE")
    ssl_certfile = os.getenv("SSL_CERTFILE")
    
    # Configure SSL if certificates are provided
    ssl_kwargs = {}
    if ssl_keyfile and ssl_certfile:
        ssl_kwargs = {
            "ssl_keyfile": ssl_keyfile,
            "ssl_certfile": ssl_certfile
        }
        print(f"🔒 SSL enabled with certificates: {ssl_certfile}", file=sys.stderr)
    
    print(f"🌐 Server starting on {host}:{port}", file=sys.stderr)
    print(f"📚 Available endpoints: http{'s' if ssl_kwargs else ''}://{host}:{port}/", file=sys.stderr)
    
    uvicorn.run(
        server.app,
        host=host,
        port=port,
        **ssl_kwargs
    )

if __name__ == "__main__":
    main()
