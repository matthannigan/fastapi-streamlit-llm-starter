# Advanced Authentication Guide

This guide explains how to extend the FastAPI-Streamlit-LLM Starter Template's simple authentication system to support advanced features like user management, role-based permissions, and rate limiting.

## 🎯 **Current Authentication System**

The starter template uses **simple API key authentication** that works well for most use cases:

```python
# Current implementation
@app.post("/process")
async def process_text(
    request: TextProcessingRequest,
    api_key: str = Depends(verify_api_key)  # Simple string validation
):
    # Process text with basic authentication
```

### Current Features:
- ✅ API key validation
- ✅ Multiple key support
- ✅ Development mode fallback
- ✅ Test mode integration
- ✅ Environment-based configuration

## 🚀 **When to Upgrade to Advanced Authentication**

Consider upgrading when you need:

- **👥 User Management**: Different users with individual accounts
- **🔒 Role-Based Access**: Admin vs User permissions
- **⚡ Rate Limiting**: Different usage limits per user type
- **📊 Usage Tracking**: Per-user analytics and billing
- **🎫 Token Management**: JWT tokens, refresh tokens, expiration
- **🏢 Enterprise Features**: SSO, LDAP integration, audit logs

## 🏗️ **Architecture Overview**

### Simple Auth (Current)
```
API Request → API Key Check → Allow/Deny
```

### Advanced Auth (Upgrade Path)
```
API Request → Token Validation → User Context → Permission Check → Rate Limit → Allow/Deny
```

## 📋 **Migration Strategy**

### Phase 1: Extend Models (Non-Breaking)

Add advanced models to `shared/models.py` alongside existing ones:

```python
# shared/models.py additions
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class UserRole(str, Enum):
    """User roles with different permission levels."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"

class UserPermission(str, Enum):
    """Granular permissions."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    BATCH_PROCESS = "batch_process"
    ANALYTICS = "analytics"

class UserContext(BaseModel):
    """Rich user context for advanced authentication."""
    user_id: str = Field(..., description="Unique user identifier")
    username: str = Field(..., description="Human-readable username")
    email: Optional[str] = Field(None, description="User email address")
    role: UserRole = Field(UserRole.USER, description="User role")
    permissions: List[UserPermission] = Field(default_factory=list, description="User permissions")
    rate_limit: int = Field(100, description="Requests per hour")
    is_active: bool = Field(True, description="Account status")
    created_at: datetime = Field(default_factory=datetime.now)
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional user metadata")

class AuthToken(BaseModel):
    """JWT token structure."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(3600, description="Token expiration in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    scope: List[str] = Field(default_factory=list, description="Token scopes")

class LoginRequest(BaseModel):
    """User login request."""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=128)
    remember_me: bool = Field(False, description="Extended session")

class UserRegistration(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)

class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    requests_made: int = Field(0, description="Requests made in current window")
    requests_remaining: int = Field(0, description="Requests remaining")
    reset_time: datetime = Field(..., description="When the rate limit resets")
    window_size: int = Field(3600, description="Rate limit window in seconds")

# Extend existing models for backward compatibility
class TextProcessingRequest(BaseModel):
    """Enhanced request model with optional user context."""
    text: str = Field(..., min_length=10, max_length=10000)
    operation: TextProcessingOperation = Field(...)
    question: Optional[str] = Field(None)
    options: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    # New fields for advanced auth (optional for backward compatibility)
    user_metadata: Optional[Dict[str, Any]] = Field(None, description="User context metadata")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Processing priority (1-10)")
```

### Phase 2: Create Advanced Auth Service

Create `backend/app/auth/advanced.py`:

```python
# backend/app/auth/advanced.py
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from redis import Redis

from shared.models import UserContext, UserRole, UserPermission, AuthToken, RateLimitInfo
from app.database import get_db  # You'll need to add database integration
from app.cache import get_redis  # You'll need to add Redis integration

class AdvancedAuthService:
    """Advanced authentication service with user management."""
    
    def __init__(self):
        self.jwt_secret = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        self.jwt_algorithm = "HS256"
        self.access_token_expire_minutes = 60
        self.refresh_token_expire_days = 30
        
        # Role-based rate limits (requests per hour)
        self.role_rate_limits = {
            UserRole.ADMIN: 10000,
            UserRole.USER: 1000,
            UserRole.READONLY: 100
        }
        
        # Role-based permissions
        self.role_permissions = {
            UserRole.ADMIN: [
                UserPermission.READ, 
                UserPermission.WRITE, 
                UserPermission.ADMIN,
                UserPermission.BATCH_PROCESS,
                UserPermission.ANALYTICS
            ],
            UserRole.USER: [
                UserPermission.READ, 
                UserPermission.WRITE,
                UserPermission.BATCH_PROCESS
            ],
            UserRole.READONLY: [UserPermission.READ]
        }
    
    def create_access_token(self, user_data: Dict[str, Any]) -> AuthToken:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        payload = {
            "sub": user_data["user_id"],
            "username": user_data["username"],
            "role": user_data["role"],
            "permissions": user_data["permissions"],
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }
        
        access_token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        return AuthToken(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes * 60,
            scope=user_data["permissions"]
        )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    async def get_user_context(
        self, 
        credentials: HTTPAuthorizationCredentials,
        db: Session,
        redis: Redis
    ) -> UserContext:
        """Get full user context from token."""
        payload = self.verify_token(credentials.credentials)
        
        # Get user from database (you'll need to implement this)
        user = await self.get_user_by_id(payload["sub"], db)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )
        
        # Check rate limits
        await self.check_rate_limit(user, redis)
        
        # Update last activity
        user.last_login = datetime.utcnow()
        db.commit()
        
        return UserContext(
            user_id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            permissions=self.role_permissions.get(user.role, []),
            rate_limit=self.role_rate_limits.get(user.role, 100),
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login,
            metadata=user.metadata or {}
        )
    
    async def check_rate_limit(self, user: UserContext, redis: Redis) -> RateLimitInfo:
        """Check and enforce rate limits."""
        key = f"rate_limit:{user.user_id}:{datetime.utcnow().hour}"
        current_requests = await redis.get(key) or 0
        current_requests = int(current_requests)
        
        if current_requests >= user.rate_limit:
            reset_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Reset at {reset_time.isoformat()}"
            )
        
        # Increment counter
        await redis.incr(key)
        await redis.expire(key, 3600)  # 1 hour expiry
        
        return RateLimitInfo(
            requests_made=current_requests + 1,
            requests_remaining=user.rate_limit - current_requests - 1,
            reset_time=datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        )
    
    def require_permission(self, required_permission: UserPermission):
        """Decorator to require specific permissions."""
        def permission_checker(user_context: UserContext = Depends(self.get_current_user)):
            if required_permission not in user_context.permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission '{required_permission}' required"
                )
            return user_context
        return permission_checker
    
    def require_role(self, required_role: UserRole):
        """Decorator to require specific role."""
        def role_checker(user_context: UserContext = Depends(self.get_current_user)):
            if user_context.role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{required_role}' required"
                )
            return user_context
        return role_checker

# Global advanced auth service
advanced_auth = AdvancedAuthService()

# Dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
    db: Session = Depends(get_db),
    redis: Redis = Depends(get_redis)
) -> UserContext:
    """Get current authenticated user context."""
    return await advanced_auth.get_user_context(credentials, db, redis)

# Permission-based dependencies
RequireAdmin = Depends(advanced_auth.require_role(UserRole.ADMIN))
RequireRead = Depends(advanced_auth.require_permission(UserPermission.READ))
RequireWrite = Depends(advanced_auth.require_permission(UserPermission.WRITE))
RequireBatchProcess = Depends(advanced_auth.require_permission(UserPermission.BATCH_PROCESS))
```

### Phase 3: Update API Endpoints

Create `backend/app/routes/advanced.py` with new endpoints:

```python
# backend/app/routes/advanced.py
from fastapi import APIRouter, Depends, HTTPException, status
from shared.models import (
    TextProcessingRequest, 
    TextProcessingResponse, 
    UserContext,
    LoginRequest,
    AuthToken,
    RateLimitInfo
)
from app.auth.advanced import get_current_user, RequireWrite, RequireBatchProcess
from app.services.text_processor import text_processor

router = APIRouter(prefix="/v2", tags=["Advanced Auth"])

@router.post("/auth/login", response_model=AuthToken)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token."""
    # Implement user authentication
    pass

@router.post("/auth/refresh", response_model=AuthToken)
async def refresh_token(refresh_token: str):
    """Refresh access token."""
    pass

@router.get("/auth/me", response_model=UserContext)
async def get_current_user_info(user: UserContext = Depends(get_current_user)):
    """Get current user information."""
    return user

@router.get("/auth/rate-limit", response_model=RateLimitInfo)
async def get_rate_limit_info(user: UserContext = Depends(get_current_user)):
    """Get current rate limit status."""
    # Return rate limit information
    pass

@router.post("/process", response_model=TextProcessingResponse)
async def process_text_advanced(
    request: TextProcessingRequest,
    user: UserContext = Depends(RequireWrite)  # Requires write permission
):
    """Process text with advanced authentication and user context."""
    # Inject user context into request
    if not request.user_metadata:
        request.user_metadata = {}
    
    request.user_metadata.update({
        "user_id": user.user_id,
        "username": user.username,
        "role": user.role,
        "processing_priority": request.priority or (10 if user.role == "admin" else 5)
    })
    
    # Process with enhanced context
    result = await text_processor.process_text(request)
    return result

@router.post("/batch-process")
async def batch_process_advanced(
    requests: List[TextProcessingRequest],
    user: UserContext = Depends(RequireBatchProcess)  # Requires batch permission
):
    """Batch process with permission checking."""
    # Enhanced batch processing with user context
    pass
```

### Phase 4: Gradual Migration

Update `backend/app/main.py` to support both auth systems:

```python
# backend/app/main.py additions
from app.routes import advanced

# Add advanced routes alongside existing ones
app.include_router(advanced.router)

# Existing simple auth endpoints remain unchanged
@app.post("/process", response_model=TextProcessingResponse)
async def process_text_simple(
    request: TextProcessingRequest,
    api_key: str = Depends(verify_api_key)  # Keep existing simple auth
):
    """Process text with simple authentication (legacy)."""
    result = await text_processor.process_text(request)
    return result

# New advanced auth endpoint
@app.post("/v2/process", response_model=TextProcessingResponse)
async def process_text_advanced(
    request: TextProcessingRequest,
    user: UserContext = Depends(get_current_user)  # New advanced auth
):
    """Process text with advanced authentication."""
    # Enhanced processing with user context
    pass
```

## 📊 **Database Integration**

### User Management Tables

```sql
-- PostgreSQL schema for user management
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    metadata JSONB DEFAULT '{}'
);

CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    permissions TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

CREATE TABLE usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    endpoint VARCHAR(100) NOT NULL,
    operation VARCHAR(50),
    processing_time FLOAT,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);
```

## 🔧 **Configuration Management**

### Advanced Environment Variables

```bash
# .env additions for advanced auth
# JWT Configuration
JWT_SECRET_KEY=your-super-secret-jwt-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/ai_processor
REDIS_URL=redis://localhost:6379

# Rate Limiting
ADMIN_RATE_LIMIT=10000
USER_RATE_LIMIT=1000
READONLY_RATE_LIMIT=100

# Security Settings
BCRYPT_ROUNDS=12
PASSWORD_MIN_LENGTH=8
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30

# Features
ENABLE_USER_REGISTRATION=true
ENABLE_PASSWORD_RESET=true
ENABLE_EMAIL_VERIFICATION=false
```

## 🧪 **Testing Advanced Auth**

### Test User Creation

```python
# tests/test_advanced_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def test_users():
    return {
        "admin": {
            "username": "admin",
            "password": "admin123",
            "role": "admin"
        },
        "user": {
            "username": "testuser",
            "password": "user123", 
            "role": "user"
        }
    }

def test_user_login(client: TestClient, test_users):
    """Test user login and token generation."""
    response = client.post("/v2/auth/login", json={
        "username": test_users["user"]["username"],
        "password": test_users["user"]["password"]
    })
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data

def test_protected_endpoint_with_token(client: TestClient, auth_headers):
    """Test accessing protected endpoint with valid token."""
    response = client.post("/v2/process", 
        json={
            "text": "Test text for processing",
            "operation": "summarize"
        },
        headers=auth_headers
    )
    assert response.status_code == 200

def test_permission_denied(client: TestClient, readonly_auth_headers):
    """Test permission denied for insufficient permissions."""
    response = client.post("/v2/process",
        json={
            "text": "Test text",
            "operation": "summarize"
        },
        headers=readonly_auth_headers
    )
    assert response.status_code == 403
```

## 📚 **Migration Checklist**

### Preparation Phase
- [ ] Add database tables for user management
- [ ] Set up Redis for caching and rate limiting
- [ ] Add JWT dependencies to requirements.txt
- [ ] Configure environment variables

### Implementation Phase
- [ ] Add advanced models to shared/models.py
- [ ] Create advanced auth service
- [ ] Add new API endpoints with versioning (/v2/)
- [ ] Update frontend for login/registration (optional)

### Testing Phase
- [ ] Create test users and roles
- [ ] Test all permission levels
- [ ] Verify rate limiting works
- [ ] Test token refresh and expiration

### Deployment Phase
- [ ] Update Docker configuration
- [ ] Add database migrations
- [ ] Configure production secrets
- [ ] Monitor and adjust rate limits

## 🚀 **Benefits of Advanced Auth**

### For Users
- **🔒 Enhanced Security**: Role-based permissions and JWT tokens
- **📊 Usage Tracking**: Detailed analytics and billing data
- **⚡ Fair Usage**: Rate limiting prevents abuse
- **👥 Team Management**: Multiple users with different access levels

### For Developers
- **🛡️ Enterprise Ready**: Meets compliance requirements
- **📈 Scalable**: Handles thousands of users
- **🔍 Auditable**: Complete request logging
- **🔌 Extensible**: Easy to add new permissions and roles

## 🎯 **Next Steps**

1. **Assess Your Needs**: Do you need user management now or later?
2. **Plan Migration**: Choose gradual vs complete migration
3. **Setup Infrastructure**: Database, Redis, monitoring
4. **Implement Gradually**: Start with core auth, add features incrementally
5. **Test Thoroughly**: Security is critical, test all edge cases

---

**Remember**: The current simple authentication system works great for many use cases. Only upgrade to advanced auth when you actually need the additional features. The architecture supports both approaches simultaneously during migration.

For questions or help with implementation, refer to the existing codebase patterns and test suites for guidance.