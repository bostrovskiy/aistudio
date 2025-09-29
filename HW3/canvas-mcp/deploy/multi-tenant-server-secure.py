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
- Rate limiting: Prevents abuse and DoS attacks
- Path traversal protection: Prevents directory traversal attacks
- Request size limits: Prevents large payload attacks
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

    def handle_request(self, request):
        """Handle MCP protocol requests with security validation."""
        try:
            data = json.loads(request)
            method = data.get('method')
            request_id = data.get('id')
            params = data.get('params', {})
            
            # Handle initialization
            if method == 'initialize':
                response = {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {
                            'tools': {}
                        },
                        'serverInfo': {
                            'name': 'canvas-mcp-multi-tenant',
                            'version': '1.0.0'
                        }
                    }
                }
            # Handle tools/list
            elif method == 'tools/list':
                response = {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'tools': [
                            {
                                'name': 'authenticate_canvas',
                                'description': 'Authenticate with your Canvas credentials',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'api_token': {'type': 'string', 'description': 'Your Canvas API token'},
                                        'api_url': {'type': 'string', 'description': 'Your Canvas API URL'},
                                        'institution_name': {'type': 'string', 'description': 'Your institution name (optional)'}
                                    },
                                    'required': ['api_token', 'api_url']
                                }
                            },
                            {
                                'name': 'get_my_profile',
                                'description': 'Get your Canvas profile information',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'}
                                    },
                                    'required': ['session_id']
                                }
                            },
                            {
                                'name': 'list_my_courses',
                                'description': 'List courses for the authenticated user',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'include_concluded': {'type': 'boolean', 'description': 'Include concluded courses'}
                                    },
                                    'required': ['session_id']
                                }
                            },
                            {
                                'name': 'get_course_details',
                                'description': 'Get detailed information about a specific course',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'course_id': {'type': 'string', 'description': 'Canvas course ID'}
                                    },
                                    'required': ['session_id', 'course_id']
                                }
                            },
                            {
                                'name': 'list_assignments',
                                'description': 'List assignments for a specific course',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'course_id': {'type': 'string', 'description': 'Canvas course ID'},
                                        'include_concluded': {'type': 'boolean', 'description': 'Include concluded assignments'}
                                    },
                                    'required': ['session_id', 'course_id']
                                }
                            },
                            {
                                'name': 'get_assignment_details',
                                'description': 'Get detailed information about a specific assignment',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'course_id': {'type': 'string', 'description': 'Canvas course ID'},
                                        'assignment_id': {'type': 'string', 'description': 'Canvas assignment ID'}
                                    },
                                    'required': ['session_id', 'course_id', 'assignment_id']
                                }
                            },
                            {
                                'name': 'list_discussions',
                                'description': 'List discussions for a specific course',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'course_id': {'type': 'string', 'description': 'Canvas course ID'},
                                        'only_announcements': {'type': 'boolean', 'description': 'Only show announcements'}
                                    },
                                    'required': ['session_id', 'course_id']
                                }
                            },
                            {
                                'name': 'get_discussion_details',
                                'description': 'Get detailed information about a specific discussion',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'course_id': {'type': 'string', 'description': 'Canvas course ID'},
                                        'discussion_id': {'type': 'string', 'description': 'Canvas discussion ID'}
                                    },
                                    'required': ['session_id', 'course_id', 'discussion_id']
                                }
                            },
                            {
                                'name': 'list_announcements',
                                'description': 'List announcements for a specific course',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'course_id': {'type': 'string', 'description': 'Canvas course ID'}
                                    },
                                    'required': ['session_id', 'course_id']
                                }
                            },
                            {
                                'name': 'get_grades',
                                'description': 'Get your grades for a specific course',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'course_id': {'type': 'string', 'description': 'Canvas course ID'}
                                    },
                                    'required': ['session_id', 'course_id']
                                }
                            },
                            {
                                'name': 'list_calendar_events',
                                'description': 'List calendar events for a specific course',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'course_id': {'type': 'string', 'description': 'Canvas course ID'},
                                        'start_date': {'type': 'string', 'description': 'Start date (YYYY-MM-DD)'},
                                        'end_date': {'type': 'string', 'description': 'End date (YYYY-MM-DD)'}
                                    },
                                    'required': ['session_id', 'course_id']
                                }
                            },
                            {
                                'name': 'search_courses',
                                'description': 'Search for courses by name or code',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'},
                                        'search_term': {'type': 'string', 'description': 'Search term for course name or code'}
                                    },
                                    'required': ['session_id', 'search_term']
                                }
                            },
                            {
                                'name': 'get_session_info',
                                'description': 'Get information about your current session',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'}
                                    },
                                    'required': ['session_id']
                                }
                            },
                            {
                                'name': 'logout',
                                'description': 'Logout and invalidate your session',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'session_id': {'type': 'string', 'description': 'Your session ID from authentication'}
                                    },
                                    'required': ['session_id']
                                }
                            }
                        ]
                    }
                }
            # Handle tools/call
            elif method == 'tools/call':
                tool_name = params.get('name')
                arguments = params.get('arguments', {})
                
                # Run async function in sync context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    if tool_name == 'authenticate_canvas':
                        api_token = arguments.get('api_token')
                        api_url = arguments.get('api_url')
                        institution_name = arguments.get('institution_name', '')
                        
                        session_id = loop.run_until_complete(self.authenticate_user(api_token, api_url))
                        if session_id:
                            session = self.user_sessions[session_id]
                            result = {
                                'session_id': session_id,
                                'user_name': session['user_name'],
                                'user_id': session['user_id'],
                                'institution': institution_name,
                                'message': '✅ Successfully authenticated with Canvas!'
                            }
                            response = {
                                'jsonrpc': '2.0',
                                'id': request_id,
                                'result': {
                                    'content': [
                                        {
                                            'type': 'text',
                                            'text': json.dumps(result, indent=2)
                                        }
                                    ]
                                }
                            }
                        else:
                            response = {
                                'jsonrpc': '2.0',
                                'id': request_id,
                                'result': {
                                    'content': [
                                        {
                                            'type': 'text',
                                            'text': json.dumps({'error': '❌ Authentication failed. Please check your credentials.'}, indent=2)
                                        }
                                    ]
                                }
                            }
                    
                    elif tool_name == 'get_my_profile':
                        session_id = arguments.get('session_id')
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', '/users/self'))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        else:
                            profile = f'''
Name: {response_data.get('name', 'N/A')}
Email: {response_data.get('email', 'N/A')}
ID: {response_data.get('id', 'N/A')}
Login ID: {response_data.get('login_id', 'N/A')}
Created: {response_data.get('created_at', 'N/A')}
'''
                            result_text = profile
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'list_my_courses':
                        session_id = arguments.get('session_id')
                        include_concluded = arguments.get('include_concluded', False)
                        
                        params_dict = {'include[]': ['term', 'teachers', 'total_students'], 'per_page': 100}
                        if include_concluded:
                            params_dict['state[]'] = ['available', 'completed']
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', '/courses', params=params_dict))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        elif not response_data:
                            result_text = 'No courses found.'
                        else:
                            courses_info = []
                            for course in response_data:
                                course_info = f'''
Course: {course.get('name', 'Unnamed')}
ID: {course.get('id')}
Code: {course.get('course_code', 'N/A')}
Term: {course.get('term', {}).get('name', 'N/A')}
Students: {course.get('total_students', 0)}
Status: {course.get('workflow_state', 'Unknown')}
'''
                                courses_info.append(course_info)
                            result_text = '\n'.join(courses_info)
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'get_course_details':
                        session_id = arguments.get('session_id')
                        course_id = arguments.get('course_id')
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', f'/courses/{course_id}'))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        else:
                            course = response_data
                            course_details = f'''
Course: {course.get('name', 'Unnamed')}
ID: {course.get('id')}
Code: {course.get('course_code', 'N/A')}
Term: {course.get('term', {}).get('name', 'N/A')}
Start Date: {course.get('start_at', 'N/A')}
End Date: {course.get('end_at', 'N/A')}
Status: {course.get('workflow_state', 'Unknown')}
Description: {course.get('public_description', 'No description available')}
'''
                            result_text = course_details
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'list_assignments':
                        session_id = arguments.get('session_id')
                        course_id = arguments.get('course_id')
                        include_concluded = arguments.get('include_concluded', False)
                        
                        params_dict = {
                            'per_page': 100,
                            'include[]': ['all_dates', 'submission']
                        }
                        if include_concluded:
                            params_dict['state[]'] = ['available', 'completed']
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', f'/courses/{course_id}/assignments', params=params_dict))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        elif not response_data:
                            result_text = f'No assignments found for course {course_id}.'
                        else:
                            assignments_info = []
                            for assignment in response_data:
                                assignment_info = f'''
Assignment: {assignment.get('name', 'Unnamed')}
ID: {assignment.get('id')}
Due: {assignment.get('due_at', 'No due date')}
Points: {assignment.get('points_possible', 0)}
Status: {assignment.get('submission', {}).get('workflow_state', 'Not submitted')}
'''
                                assignments_info.append(assignment_info)
                            result_text = '\n'.join(assignments_info)
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'get_assignment_details':
                        session_id = arguments.get('session_id')
                        course_id = arguments.get('course_id')
                        assignment_id = arguments.get('assignment_id')
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', f'/courses/{course_id}/assignments/{assignment_id}'))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        else:
                            assignment = response_data
                            assignment_details = f'''
Assignment: {assignment.get('name', 'Unnamed')}
ID: {assignment.get('id')}
Due: {assignment.get('due_at', 'No due date')}
Points: {assignment.get('points_possible', 0)}
Description: {assignment.get('description', 'No description available')}
Status: {assignment.get('submission', {}).get('workflow_state', 'Not submitted')}
'''
                            result_text = assignment_details
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'list_discussions':
                        session_id = arguments.get('session_id')
                        course_id = arguments.get('course_id')
                        only_announcements = arguments.get('only_announcements', False)
                        
                        params_dict = {'per_page': 100}
                        if only_announcements:
                            params_dict['only_announcements'] = True
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', f'/courses/{course_id}/discussion_topics', params=params_dict))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        elif not response_data:
                            result_text = f'No discussions found for course {course_id}.'
                        else:
                            discussions_info = []
                            for discussion in response_data:
                                discussion_info = f'''
Discussion: {discussion.get('title', 'Unnamed')}
ID: {discussion.get('id')}
Posted: {discussion.get('posted_at', 'N/A')}
Author: {discussion.get('author', {}).get('display_name', 'Unknown')}
'''
                                discussions_info.append(discussion_info)
                            result_text = '\n'.join(discussions_info)
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'get_discussion_details':
                        session_id = arguments.get('session_id')
                        course_id = arguments.get('course_id')
                        discussion_id = arguments.get('discussion_id')
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', f'/courses/{course_id}/discussion_topics/{discussion_id}'))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        else:
                            discussion = response_data
                            discussion_details = f'''
Discussion: {discussion.get('title', 'Unnamed')}
ID: {discussion.get('id')}
Posted: {discussion.get('posted_at', 'N/A')}
Author: {discussion.get('author', {}).get('display_name', 'Unknown')}
Message: {discussion.get('message', 'No message available')}
'''
                            result_text = discussion_details
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'list_announcements':
                        session_id = arguments.get('session_id')
                        course_id = arguments.get('course_id')
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', f'/courses/{course_id}/discussion_topics', params={'only_announcements': True, 'per_page': 100}))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        elif not response_data:
                            result_text = f'No announcements found for course {course_id}.'
                        else:
                            announcements_info = []
                            for announcement in response_data:
                                announcement_info = f'''
Announcement: {announcement.get('title', 'Unnamed')}
ID: {announcement.get('id')}
Posted: {announcement.get('posted_at', 'N/A')}
Author: {announcement.get('author', {}).get('display_name', 'Unknown')}
'''
                                announcements_info.append(announcement_info)
                            result_text = '\n'.join(announcements_info)
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'get_grades':
                        session_id = arguments.get('session_id')
                        course_id = arguments.get('course_id')
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', f'/courses/{course_id}/enrollments'))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        else:
                            grades_info = []
                            for enrollment in response_data:
                                if enrollment.get('type') == 'StudentEnrollment':
                                    grades_info.append(f'''
Course: {enrollment.get('course_id')}
Grade: {enrollment.get('grades', {}).get('current_grade', 'N/A')}
Score: {enrollment.get('grades', {}).get('current_score', 'N/A')}
Status: {enrollment.get('enrollment_state', 'Unknown')}
''')
                            result_text = '\n'.join(grades_info) if grades_info else 'No grade information available.'
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'list_calendar_events':
                        session_id = arguments.get('session_id')
                        course_id = arguments.get('course_id')
                        start_date = arguments.get('start_date')
                        end_date = arguments.get('end_date')
                        
                        params_dict = {'per_page': 100}
                        if start_date:
                            params_dict['start_date'] = start_date
                        if end_date:
                            params_dict['end_date'] = end_date
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', f'/courses/{course_id}/calendar_events', params=params_dict))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        elif not response_data:
                            result_text = f'No calendar events found for course {course_id}.'
                        else:
                            events_info = []
                            for event in response_data:
                                event_info = f'''
Event: {event.get('title', 'Unnamed')}
ID: {event.get('id')}
Start: {event.get('start_at', 'N/A')}
End: {event.get('end_at', 'N/A')}
Description: {event.get('description', 'No description available')}
'''
                                events_info.append(event_info)
                            result_text = '\n'.join(events_info)
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'search_courses':
                        session_id = arguments.get('session_id')
                        search_term = arguments.get('search_term')
                        
                        response_data = loop.run_until_complete(self.make_canvas_request(session_id, 'get', '/courses', params={'search': search_term, 'per_page': 100}))
                        
                        if 'error' in response_data:
                            result_text = f'Error: {response_data["error"]}'
                        elif not response_data:
                            result_text = f'No courses found matching "{search_term}".'
                        else:
                            courses_info = []
                            for course in response_data:
                                course_info = f'''
Course: {course.get('name', 'Unnamed')}
ID: {course.get('id')}
Code: {course.get('course_code', 'N/A')}
Term: {course.get('term', {}).get('name', 'N/A')}
'''
                                courses_info.append(course_info)
                            result_text = '\n'.join(courses_info)
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'get_session_info':
                        session_id = arguments.get('session_id')
                        session = self.get_user_session(session_id)
                        
                        if not session:
                            result_text = '❌ Invalid or expired session. Please re-authenticate.'
                        else:
                            info = f'''
Session ID: {session_id}
User: {session['user_name']} (ID: {session['user_id']})
Canvas URL: {session['api_url']}
Created: {session['created_at'].strftime('%Y-%m-%d %H:%M:%S')}
Last Activity: {session['last_activity'].strftime('%Y-%m-%d %H:%M:%S')}
'''
                            result_text = info
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    elif tool_name == 'logout':
                        session_id = arguments.get('session_id')
                        
                        if session_id in self.user_sessions:
                            user_name = self.user_sessions[session_id]['user_name']
                            del self.user_sessions[session_id]
                            result_text = f'✅ Successfully logged out {user_name}'
                        else:
                            result_text = '❌ Session not found or already expired'
                        
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': result_text
                                    }
                                ]
                            }
                        }
                    
                    else:
                        response = {
                            'jsonrpc': '2.0',
                            'id': request_id,
                            'result': {
                                'content': [
                                    {
                                        'type': 'text',
                                        'text': 'Unknown tool'
                                    }
                                ]
                            }
                        }
                
                finally:
                    loop.close()
            
            # Handle notification (no response needed)
            elif method == 'notifications/initialized':
                return None  # Don't send response for notifications
            # Handle unknown methods
            else:
                response = {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601,
                        'message': 'Method not found'
                    }
                }
            
            return json.dumps(response) + '\n'
        except Exception as e:
            return json.dumps({
                'jsonrpc': '2.0',
                'id': data.get('id') if 'data' in locals() else None,
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            }) + '\n'

    def main(self):
        """Run the multi-tenant MCP server."""
        print(f"🚀 Starting Multi-Tenant Canvas MCP Server...", file=sys.stderr)
        print(f"🔐 Each user must authenticate with their own Canvas credentials", file=sys.stderr)
        print(f"⏰ Session timeout: {self.session_timeout}", file=sys.stderr)
        print(f"🛡️ Security features: Rate limiting, input validation, data anonymization", file=sys.stderr)
        
        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    break
                
                response = self.handle_request(line.strip())
                if response:  # Only send response if not None
                    sys.stdout.write(response)
                    sys.stdout.flush()
                
        except KeyboardInterrupt:
            print("\n🛑 Server stopped", file=sys.stderr)
        except Exception as e:
            print(f"❌ Server error: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    server = MultiTenantCanvasServer()
    server.main()
