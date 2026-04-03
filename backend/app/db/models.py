# =========================
# db/models.py
# =========================
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
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
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    action = Column(String, nullable=False)
    details = Column(Text)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, nullable=False)
    signal_type = Column(String, nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float, nullable=False)
    price = Column(Float)
    strategy = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MarketData(Base):
    """Store live market data fetched every 30 seconds"""
    __tablename__ = "market_data"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    coin = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    price = Column(Float, nullable=False)
    volume = Column(Float, default=0)
    change_24h = Column(Float, default=0)


class Prediction(Base):
    """Store AI predictions generated every 5 minutes"""
    __tablename__ = "predictions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    coin = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    current_price = Column(Float, nullable=False)
    predicted_direction = Column(String, nullable=False)  # BUY, SELL, HOLD
    confidence = Column(Float, nullable=False)
    target_price = Column(Float)
    timeframe = Column(String, default="1h")  # 1h, 4h, 1d


class Portfolio(Base):
    __tablename__ = "portfolio"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    balance = Column(Float, default=10000.0)
    total_equity = Column(Float, default=10000.0)
    available_balance = Column(Float, default=10000.0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
