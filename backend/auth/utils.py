import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from passlib.context import CryptContext
from jose import jwt

SECRET = "SECRET_KEY"
pwd = CryptContext(schemes=["bcrypt"])

def hash_password(p):
    return pwd.hash(p)

def verify(p, h):
    return pwd.verify(p, h)

def create_token(data):
    return jwt.encode(data, SECRET, algorithm="HS256")
