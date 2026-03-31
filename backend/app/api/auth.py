# =========================
# api/auth.py
# =========================
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.security import hash_password, verify_password, create_token, verify_token
from app.db.models import User
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

# In-memory user store for demo (replace with database)
users_db = {
    "admin": {
        "id": 1,
        "username": "admin",
        "password": hash_password("admin123"),
        "role": "ADMIN",
        "email": "admin@example.com"
    },
    "user": {
        "id": 2,
        "username": "user",
        "password": hash_password("user123"),
        "role": "USER",
        "email": "user@example.com"
    }
}

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "USER"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate user and return JWT token"""
    user = users_db.get(request.username)
    
    if not user or not verify_password(request.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token_data = {
        "user": user["username"],
        "role": user["role"],
        "user_id": user["id"]
    }
    access_token = create_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "role": user["role"],
            "email": user["email"]
        }
    }

@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """Register new user"""
    if request.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user
    new_user = {
        "id": len(users_db) + 1,
        "username": request.username,
        "email": request.email,
        "password": hash_password(request.password),
        "role": request.role
    }
    
    users_db[request.username] = new_user
    
    # Create token
    token_data = {
        "user": new_user["username"],
        "role": new_user["role"],
        "user_id": new_user["id"]
    }
    access_token = create_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": new_user["username"],
            "role": new_user["role"],
            "email": new_user["email"]
        }
    }

@router.get("/me")
async def get_current_user_info(token: str):
    """Get current user info from token"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = users_db.get(payload.get("user"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "username": user["username"],
        "role": user["role"],
        "email": user["email"]
    }

@router.post("/refresh")
async def refresh_token(token: str):
    """Refresh JWT token"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = users_db.get(payload.get("user"))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create new token
    token_data = {
        "user": user["username"],
        "role": user["role"],
        "user_id": user["id"]
    }
    access_token = create_token(token_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
