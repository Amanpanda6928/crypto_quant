# =========================
# db/models.py
# =========================
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    role = Column(String, default="USER")  # USER, ADMIN, SUPERADMIN
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    symbol = Column(String, nullable=False)
    type = Column(String, nullable=False)  # BUY, SELL
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    status = Column(String, default="OPEN")  # OPEN, CLOSED, CANCELLED
    strategy = Column(String)
    confidence = Column(Float)
    pnl = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True))

class AuditLog(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    signal_type = Column(String, nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float, nullable=False)
    price = Column(Float)
    strategy = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Portfolio(Base):
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    balance = Column(Float, default=10000.0)
    total_equity = Column(Float, default=10000.0)
    available_balance = Column(Float, default=10000.0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
