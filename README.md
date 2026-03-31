# CryptoQuant AI Trading Platform

A comprehensive AI-powered cryptocurrency trading platform with real-time predictions, backtesting, and live trading capabilities.

## Project Structure

```
CryptoQuant/
├── 📁 frontend/                 # React + Vite Frontend
│   ├── 📁 public/              # Static assets
│   │   ├── favicon.ico
│   │   ├── index.html
│   │   └── robots.txt
│   ├── 📁 src/
│   │   ├── 📁 api/             # API integration
│   │   ├── 📁 components/      # React components
│   │   │   ├── auth/
│   │   │   ├── charts/
│   │   │   ├── layout/
│   │   │   ├── trading/
│   │   │   └── ui/
│   │   ├── 📁 context/         # React context
│   │   ├── 📁 hooks/           # Custom hooks
│   │   ├── 📁 layout/          # Layout components
│   │   ├── 📁 pages/           # Page components
│   │   ├── 📁 services/        # Service layer
│   │   ├── 📁 styles/          # CSS/SCSS files
│   │   ├── 📁 utils/           # Utility functions
│   │   ├── App.jsx             # Main app component
│   │   ├── App.css
│   │   ├── index.css           # Global styles
│   │   └── main.jsx            # Entry point
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
│
├── 📁 backend/                  # Python FastAPI Backend
│   ├── 📁 api/                 # API endpoints
│   ├── 📁 config/              # Configuration
│   ├── 📁 core/                # Core business logic
│   ├── 📁 data/                # Data storage
│   ├── 📁 services/            # Service layer
│   ├── 📁 utils/               # Utility functions
│   ├── 📁 tests/               # Test suite
│   ├── main.py                 # FastAPI main app
│   └── requirements.txt
│
├── 📁 docs/                     # Documentation
├── 📁 scripts/                  # Automation scripts
├── .gitignore
├── requirements.txt            # Root dependencies
└── README.md                   # This file
```

## Quick Start

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

## Features

- **Live Trading Chart** - Candlestick charts with 1-hour predictions
- **AI Predictions** - 5m, 15m, 30m, 1h future price predictions
- **Backtesting** - Strategy testing with MA crossover, RSI, MACD, Bollinger Bands
- **30+ Crypto Coins** - BTC, ETH, BNB, SOL, ADA, and more
- **Real-time Data** - Live price feeds with WebSocket support
- **Authentication** - Mock auth with JWT tokens

## Tech Stack

**Frontend:** React 18 + Vite, TailwindCSS, Recharts, Axios  
**Backend:** Python FastAPI, LSTM Neural Networks, Binance API, NumPy/Pandas

## Login Credentials

- **Email:** admin@nexus.ai
- **Password:** 123456
- **Role:** Admin ELITE

## 30 Supported Coins

BTC, ETH, BNB, SOL, ADA, DOT, DOGE, AVAX, MATIC, LINK, UNI, LTC, BCH, XLM, VET, FIL, TRX, ETC, XMR, AAVE, ALGO, ATOM, AXS, FTM, SAND, MANA, GALA, RUNE
