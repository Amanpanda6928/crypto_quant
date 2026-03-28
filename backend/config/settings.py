import os
from dotenv import load_dotenv

load_dotenv()

# ==============================
# APP CONFIG
# ==============================
APP_NAME = "CryptoQuant AI"
DEBUG = True

# ==============================
# SERVER
# ==============================
HOST = "0.0.0.0"
PORT = 8000

# ==============================
# DATABASE
# ==============================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/crypto_quant"
)

# ==============================
# AUTH / SECURITY
# ==============================
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

# ==============================
# TRADING CONFIG
# ==============================
COINS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT",
    "TRXUSDT", "AVAXUSDT", "LINKUSDT", "ATOMUSDT", "ETCUSDT",
    "FILUSDT", "ICPUSDT", "APTUSDT", "NEARUSDT", "ALGOUSDT",
    "VETUSDT", "SANDUSDT", "MANAUSDT", "AXSUSDT", "EGLDUSDT",
    "FTMUSDT", "THETAUSDT", "HBARUSDT", "XLMUSDT", "KAVAUSDT"
]

TIMEFRAMES = ["1m", "5m", "15m", "1h"]

# ==============================
# MODEL PATHS
# ==============================
MODEL_DIR = os.getenv("MODEL_DIR", "backend/ml/models")

# ==============================
# API (Binance or others)
# ==============================
BINANCE_BASE_URL = "https://api.binance.com"

# ==============================
# SIGNAL THRESHOLDS
# ==============================
BUY_THRESHOLD = 0.5
SELL_THRESHOLD = -0.5
HOLD_THRESHOLD = 0.1

# Legacy compatibility
PREDICTION_WEIGHTS = {
    "1m": 0.1,
    "5m": 0.2, 
    "15m": 0.3,
    "1h": 0.4
}
CONFIDENCE_STRONG = 90
CONFIDENCE_MEDIUM = 70
