# =========================
# api/auth.py
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.security import hash_password, verify_password, create_token, verify_token
from app.db.models import User
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()

# In-memory user store for demo (replace with database)
users_db = {
    "amandeep": {
        "id": 1,
        "username": "amandeep",
        "password": hash_password("admin123"),
        "role": "ADMIN",
        "email": "amandeep@nexus.ai",
        "name": "Amandeep"
    },
    "karan": {
        "id": 2,
        "username": "karan",
        "password": hash_password("user123"),
        "role": "USER",
        "email": "karan@nexus.ai",
        "name": "Karan Sahoo"
    },
    "biswajit": {
        "id": 3,
        "username": "biswajit",
        "password": hash_password("user123"),
        "role": "USER",
        "email": "biswajit@nexus.ai",
        "name": "Biswajit Das"
    },
    "gudu": {
        "id": 4,
        "username": "gudu",
        "password": hash_password("user123"),
        "role": "USER",
        "email": "gudu@nexus.ai",
        "name": "Priyabata Pradhan"
    }
}

from typing import Optional

class LoginRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None  # Optional for login

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
