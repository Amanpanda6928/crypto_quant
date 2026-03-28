from fastapi import APIRouter
from db.database import SessionLocal
from db.models import User
from auth.utils import hash_password, verify, create_token

router = APIRouter()

@router.post("/register")
def register(user: dict):
    db = SessionLocal()

    u = User(
        username=user["username"],
        password=hash_password(user["password"]),
        role="user"
    )

    db.add(u)
    db.commit()

    return {"status": "created"}


@router.post("/login")
def login(user: dict):
    db = SessionLocal()

    u = db.query(User).filter(User.username == user["username"]).first()

    if not u or not verify(user["password"], u.password):
        return {"status": "fail"}

    token = create_token({"user": u.username})

    return {
        "status": "success",
        "token": token,
        "role": u.role
    }
