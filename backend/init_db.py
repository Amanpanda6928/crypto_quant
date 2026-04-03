#!/usr/bin/env python3
"""Initialize database tables"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

# Import all models first
from db.database import init_db, engine
from db.models import Base, User, Trade, MarketData, Prediction, Signal

# Create all tables
print("Creating database tables...")
Base.metadata.create_all(bind=engine)
print("Database initialized successfully!")
