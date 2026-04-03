from sqlalchemy import Column, Integer, String, Float, DateTime
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from db.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String)


class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    symbol = Column(String)
    action = Column(String)
    price = Column(Float)
    pnl = Column(Float)


class MarketData(Base):
    """Store live market data fetched every 30 seconds"""
    __tablename__ = "market_data"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    coin = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    price = Column(Float)
    volume = Column(Float)
    change_24h = Column(Float)


class Prediction(Base):
    """Store AI predictions generated every 5 minutes"""
    __tablename__ = "predictions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    coin = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    current_price = Column(Float)
    predicted_direction = Column(String)  # BUY, SELL, HOLD
    confidence = Column(Float)
    target_price = Column(Float)
    timeframe = Column(String)  # 1h, 4h, 1d


class Signal(Base):
    """Store high-confidence trading signals"""
    __tablename__ = "signals"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True)
    coin = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.now)
    signal = Column(String)  # BUY, SELL, HOLD
    confidence = Column(Float)
    current_price = Column(Float)
    target_price = Column(Float)
    reason = Column(String)
