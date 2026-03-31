# =========================
# core/security.py
# =========================
import os
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional
from app.core.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Use bcrypt directly to avoid passlib compatibility issues
try:
    import bcrypt
    
    def hash_password(password: str) -> str:
        # Encode to bytes and hash
        password_bytes = password.encode('utf-8')
        # bcrypt has 72 byte limit
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    def verify_password(password: str, hashed_password: str) -> bool:
        try:
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
            
except ImportError:
    # Fallback if bcrypt not available
    def hash_password(password: str) -> str:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(password: str, hashed_password: str) -> bool:
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed_password

def create_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(token: str) -> dict:
    payload = verify_token(token)
    if payload is None:
        return None
    return payload
