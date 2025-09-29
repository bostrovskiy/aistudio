# 🔐 Canvas MCP Server Security Models

This document explains different security models for the Canvas MCP Server and their implications.

## 🚨 **Security Problem You Identified**

You're absolutely correct! The current single-tenant model has a critical security flaw:

### **❌ Single-Tenant Model (Current)**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User A        │    │   MCP Server     │    │   Your Canvas   │
│   (Claude)      │───▶│   (Your Token)   │───▶│   Account       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
┌─────────────────┐           │
│   User B        │───────────┘
│   (Claude)      │
└─────────────────┘
```

**Problems:**
- 🔴 **Shared Credentials**: Everyone uses YOUR Canvas token
- 🔴 **No Isolation**: All users see YOUR Canvas data
- 🔴 **Audit Issues**: Canvas logs show all activity under YOUR account
- 🔴 **Permission Escalation**: Users could access data you don't want them to see

## ✅ **Multi-Tenant Model (Recommended)**

### **🔐 Per-User Authentication**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User A        │    │   MCP Server     │    │   User A's      │
│   (Claude)      │───▶│   (Session A)    │───▶│   Canvas        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User B        │    │   MCP Server     │    │   User B's      │
│   (Claude)      │───▶│   (Session B)    │───▶│   Canvas        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Benefits:**
- ✅ **Isolated Credentials**: Each user provides their own Canvas token
- ✅ **Data Isolation**: Users only see their own Canvas data
- ✅ **Proper Audit Trail**: Canvas logs show activity under each user's account
- ✅ **No Permission Escalation**: Users can't access data they shouldn't see

## 🛡️ **Security Models Comparison**

| Aspect | Single-Tenant | Multi-Tenant | Hybrid |
|--------|---------------|--------------|---------|
| **Credential Sharing** | ❌ Shared | ✅ Isolated | ✅ Isolated |
| **Data Isolation** | ❌ None | ✅ Complete | ✅ Complete |
| **Audit Trail** | ❌ Confused | ✅ Clear | ✅ Clear |
| **Setup Complexity** | ✅ Simple | ⚠️ Moderate | ⚠️ Moderate |
| **User Experience** | ✅ No auth needed | ⚠️ Auth required | ⚠️ Auth required |
| **Security Level** | 🔴 Low | 🟢 High | 🟢 High |

## 🔧 **Implementation Options**

### **Option 1: Multi-Tenant Server (Recommended)**

**How it works:**
1. Each user authenticates with their own Canvas credentials
2. Server creates isolated sessions
3. All API calls use the user's own credentials
4. Sessions expire after 24 hours

**Implementation:**
```python
# User authenticates with their own credentials
session_id = await authenticate_canvas(
    api_token="user_own_token",
    api_url="https://user_school.canvas.edu/api/v1"
)

# All subsequent calls use their session
courses = await list_my_courses(session_id)
```

**Benefits:**
- ✅ Complete credential isolation
- ✅ Proper audit trails
- ✅ No shared data access
- ✅ FERPA compliant

### **Option 2: Hybrid Model**

**How it works:**
1. Server has a "default" Canvas account (yours)
2. Users can optionally provide their own credentials
3. If no credentials provided, uses default account
4. If credentials provided, uses user's account

**Implementation:**
```python
# Optional authentication
if user_provides_credentials:
    session_id = await authenticate_canvas(user_token, user_url)
    # Use user's credentials
else:
    # Use default credentials (yours)
    session_id = "default"
```

**Benefits:**
- ✅ Backward compatibility
- ✅ Optional user authentication
- ✅ Gradual migration path

### **Option 3: Role-Based Access**

**How it works:**
1. You define user roles and permissions
2. Users authenticate with their own credentials
3. Server checks permissions before allowing access
4. Different users see different data based on roles

**Implementation:**
```python
# Role-based access control
if user_role == "student":
    # Only see their own data
    data = await get_student_data(session_id)
elif user_role == "instructor":
    # See course data they teach
    data = await get_instructor_data(session_id)
```

## 🚀 **Deployment Recommendations**

### **For Personal Use (Just You)**
- ✅ **Single-Tenant**: Simple, no authentication needed
- ✅ **Your credentials only**: No security concerns

### **For Team/Organization Use**
- ✅ **Multi-Tenant**: Each person uses their own credentials
- ✅ **Complete isolation**: No shared data access
- ✅ **Proper audit trails**: Clear accountability

### **For Public/Open Use**
- ✅ **Multi-Tenant**: Required for security
- ✅ **User authentication**: Each user provides credentials
- ✅ **Session management**: Automatic cleanup of expired sessions

## 🔐 **Security Best Practices**

### **1. Credential Management**
```python
# ✅ Good: Per-user credentials
user_session = await authenticate_user(user_token, user_url)

# ❌ Bad: Shared credentials
shared_token = "everyone_uses_this_token"
```

### **2. Session Security**
```python
# ✅ Good: Session timeouts
if session_expired(session_id):
    return {"error": "Session expired, please re-authenticate"}

# ✅ Good: Secure session IDs
session_id = secrets.token_urlsafe(32)
```

### **3. Data Isolation**
```python
# ✅ Good: User-specific data
user_courses = await get_courses_for_user(session_id)

# ❌ Bad: Shared data
all_courses = await get_all_courses()  # Everyone sees everything
```

## 📋 **Migration Guide**

### **From Single-Tenant to Multi-Tenant**

1. **Deploy Multi-Tenant Server**
   ```bash
   # Deploy the new server
   python deploy/multi-tenant-server.py
   ```

2. **Update Client Configuration**
   ```json
   {
     "mcpServers": {
       "canvas-multi-tenant": {
         "command": "python",
         "args": ["deploy/multi-tenant-server.py"]
       }
     }
   }
   ```

3. **User Authentication Flow**
   ```python
   # First, authenticate
   auth_result = await authenticate_canvas(
       api_token="user_token",
       api_url="user_canvas_url"
   )
   
   # Then use the session
   courses = await list_my_courses(session_id)
   ```

## 🎯 **Recommendation**

**For your use case, I recommend the Multi-Tenant model because:**

1. **🔐 Security**: Each user's credentials are isolated
2. **📊 Audit Trail**: Clear accountability in Canvas logs
3. **🛡️ FERPA Compliance**: No unauthorized data access
4. **🔄 Scalable**: Can handle multiple users safely
5. **⚖️ Fair**: Each user sees only their own data

The multi-tenant server I created handles all the security concerns you raised while maintaining a good user experience!
