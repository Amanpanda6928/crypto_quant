# =========================
# core/config.py
# =========================
import os
from typing import Optional

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
LIVE_TRADING = False

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/cryptodb")

# Trading settings
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
DEFAULT_RISK_PERCENTAGE = 2.0
MAX_POSITION_SIZE = 0.1  # 10% of portfolio

# Bot settings
BOT_INTERVAL = 5  # seconds
MAX_DAILY_TRADES = 50

# JWT settings
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Risk management
MAX_DRAWDOWN = 0.15  # 15%
MIN_WIN_RATE = 0.4  # 40%
