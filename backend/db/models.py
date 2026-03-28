from sqlalchemy import Column, Integer, String, Float
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)


class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    symbol = Column(String)
    action = Column(String)
    price = Column(Float)
    pnl = Column(Float)
