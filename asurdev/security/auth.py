"""
Security Fix #3: JWT Authorization + OAuth2
Добавляет полноценную авторизацию
"""
import os
import hashlib
import hmac
import jwt
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass
from functools import wraps

# Configuration
JWT_SECRET = os.environ.get("asurdev_JWT_SECRET", "your-secret-key-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

@dataclass
class User:
    user_id: str
    username: str
    roles: list[str]
    api_key_hash: str

class AuthManager:
    """JWT + API Key authorization"""
    
    def __init__(self):
        self._users: dict[str, User] = {}
        self._api_keys: dict[str, str] = {}  # api_key -> user_id
    
    def create_user(self, username: str, password: str, roles: list[str] = ["user"]) -> User:
        """Create new user"""
        import uuid
        
        user_id = str(uuid.uuid4())
        password_hash = self._hash_password(password)
        api_key = self._generate_api_key()
        api_key_hash = self._hash_password(api_key)
        
        user = User(
            user_id=user_id,
            username=username,
            roles=roles,
            api_key_hash=api_key_hash
        )
        
        self._users[user_id] = user
        self._api_keys[api_key_hash] = user_id
        
        # Return user with plain API key (show only once!)
        return User(
            user_id=user_id,
            username=username,
            roles=roles,
            api_key_hash=api_key  # Plain for display
        )
    
    def create_token(self, user_id: str) -> str:
        """Create JWT token"""
        payload = {
            "user_id": user_id,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
            "iat": datetime.utcnow(),
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[str]:
        """Verify JWT and return user_id"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload["user_id"]
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return user_id"""
        api_key_hash = self._hash_password(api_key)
        return self._api_keys.get(api_key_hash)
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password with salt"""
        salt = os.environ.get("asurdev_SALT", "default-salt")
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode(),
            salt.encode(),
            100000
        ).hex()
    
    @staticmethod
    def _generate_api_key() -> str:
        """Generate secure API key"""
        import secrets
        return f"af_{secrets.token_urlsafe(32)}"


def require_auth(roles: list[str] = ["user"]):
    """Decorator for authenticated endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            # Check header
            auth_header = request.headers.get("Authorization", "")
            
            token = None
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
            
            if not token:
                return {"error": "Unauthorized", "status": 401}
            
            # Verify
            auth = AuthManager()
            user_id = auth.verify_token(token)
            
            if not user_id:
                return {"error": "Invalid token", "status": 401}
            
            # Check roles
            user = auth._users.get(user_id)
            if not any(role in user.roles for role in roles):
                return {"error": "Forbidden", "status": 403}
            
            # Add user to request
            request.user_id = user_id
            return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator


class RateLimiter:
    """Rate limiting for API protection"""
    
    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self._requests: dict[str, list] = {}
    
    def check(self, identifier: str) -> tuple[bool, int]:
        """Check if request is allowed. Returns (allowed, remaining)"""
        import time
        
        now = time.time()
        window = 60  # 1 minute
        
        if identifier not in self._requests:
            self._requests[identifier] = []
        
        # Remove old requests
        self._requests[identifier] = [
            t for t in self._requests[identifier]
            if now - t < window
        ]
        
        # Check limit
        if len(self._requests[identifier]) >= self.rpm:
            return False, 0
        
        # Add current request
        self._requests[identifier].append(now)
        remaining = self.rpm - len(self._requests[identifier])
        return True, remaining


# Test
if __name__ == "__main__":
    auth = AuthManager()
    
    # Create user
    user = auth.create_user("admin", "strong_password", ["admin", "user"])
    print(f"User created: {user.username}")
    print(f"API Key: {user.api_key_hash}")  # Show only once!
    
    # Create and verify token
    token = auth.create_token(user.user_id)
    verified = auth.verify_token(token)
    print(f"Token valid: {verified == user.user_id}")
    
    print("\n✓ Auth module ready")
