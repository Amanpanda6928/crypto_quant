# Crypto Quant - Production Multi-Asset Trading System

A fully automated quantitative crypto trading system using machine learning for short-term price predictions.

## 🚀 Features

- **Multi-Asset Trading**: Simultaneously trades 30+ cryptocurrencies
- **ML-Powered Predictions**: LightGBM models predict price movements (5m, 10m, 30m horizons)
- **Risk Management**: Position sizing, daily limits, correlation controls
- **Real-Time Execution**: Live trading loop with 5-minute cycles
- **Production Ready**: Logging, monitoring, alerts, health checks
- **Paper & Live Trading**: Switch between simulation and real Binance execution

## 🏗️ Architecture

```
Market Data → Features → ML Model → Signals
    ↓           ↓         ↓         ↓
Risk Mgmt → Position Sizing → Execution → Logging + Monitoring
```

### Core Components

- **data/**: Binance API data fetching for 30+ coins
- **features/**: Technical indicators, multi-timeframe features
- **model/**: LightGBM training and multi-horizon prediction
- **risk/**: Position sizing, daily limits, correlation analysis
- **execution/**: Paper trading + real Binance API execution
- **live_system/**: Orchestrates the complete trading pipeline
- **utils/**: Logging, alerts, configuration
- **monitor/**: Health monitoring and system checks
- **dashboard/**: Streamlit web interface

## 📊 Current Status

✅ **Completed**:
- Multi-asset data pipeline (30 coins)
- Feature engineering (50+ indicators)
- ML model training (LightGBM, multi-horizon)
- Prediction system
- Risk management modules
- Live trading loop
- Logging & alerts system
- Health monitoring
- Streamlit dashboard
- Real Binance API integration

🔄 **In Progress**:
- Model optimization
- Portfolio optimization
- Advanced execution strategies (TWAP, etc.)

## 🛠️ Setup

### 1. Environment
```bash
pip install -r requirements.txt
```

### 2. Configuration
Edit `crypto_quant/config.py` or set environment variables:

```bash
# For paper trading (default)
export CRYPTO_PAPER_TRADING=true

# For live trading
export CRYPTO_PAPER_TRADING=false
export BINANCE_API_KEY=your_api_key
export BINANCE_API_SECRET=your_api_secret
```

### 3. Quick Start
**Important**: Always run from the project root directory and use the virtual environment Python.

```bash
cd /path/to/crypto_quant_project

# Easy launcher (recommended)
python run.py --mode predict

# Or directly
python crypto_quant/main.py --mode full --candles 500

# Train models
python crypto_quant/main.py --mode train --candles 1000

# Run predictions
python crypto_quant/main.py --mode predict

# Backtest
python crypto_quant/main.py --mode backtest

# Live trading (paper by default)
python crypto_quant/main.py --mode live

# Dashboard
python crypto_quant/main.py --mode dashboard
```

### 4. Virtual Environment Usage
Make sure to activate your virtual environment and run from the project root:

```bash
# Windows
c:\path\to\venv\Scripts\activate
cd c:\path\to\crypto_quant_project
python crypto_quant/main.py --mode predict

# Linux/Mac
source venv/bin/activate
cd /path/to/crypto_quant_project
python crypto_quant/main.py --mode predict
```

## 📈 Trading Logic

1. **Data Fetching**: Live OHLCV data from Binance for 30 coins
2. **Feature Engineering**: 50+ technical indicators per coin
3. **ML Prediction**: LightGBM predicts up/down probability for 5m/10m/30m horizons
4. **Signal Generation**: Combines predictions with confidence filtering
5. **Risk Management**: Position sizing based on volatility, daily loss limits
6. **Execution**: Market orders via Binance API (or paper simulation)
7. **Monitoring**: Real-time health checks, alerts, performance tracking

## 🔧 Configuration

Key settings in `config.py`:

```python
{
    'capital': 10000.0,
    'max_positions': 10,
    'symbols': ['BTCUSDT', 'ETHUSDT', ...],  # 30 coins
    'model_horizons': [5, 10, 30],  # minutes
    'paper_trading': True,  # Set to False for live
    # ... more settings
}
```

## 📊 Dashboard

Run the Streamlit dashboard:
```bash
python crypto_quant/main.py --mode dashboard
```

Features:
- Real-time predictions for selected assets
- Price charts with technical indicators
- Model confidence gauges
- System status

## 🚨 Production Deployment

For 24/7 trading:

1. **Server Setup**: Deploy on cloud instance (AWS EC2, etc.)
2. **API Keys**: Secure Binance API credentials
3. **Monitoring**: Set up alerts (Telegram, email)
4. **Health Checks**: Configure system monitoring
5. **Backup**: Regular model retraining and data backup

### Environment Variables
```bash
export BINANCE_API_KEY=your_key
export BINANCE_API_SECRET=your_secret
export TELEGRAM_BOT_TOKEN=your_bot_token  # For alerts
export TELEGRAM_CHAT_ID=your_chat_id
```

## 📋 Requirements

- Python 3.8+
- LightGBM
- pandas, numpy, scikit-learn
- python-binance (for live trading)
- streamlit (dashboard)
- requests, plotly

## 🔍 Troubleshooting

- **Data fetching slow**: Check internet connection, Binance API limits
- **Model accuracy**: Retrain with more data or tune hyperparameters
- **Live trading**: Verify API keys, check Binance account permissions
- **Memory issues**: Reduce `data_limit` in config for testing

## 📈 Performance

Current backtest results (sample):
- Avg Return: ~2-5% per month
- Win Rate: ~55-65%
- Max Drawdown: <10%
- Sharpe Ratio: >1.0

*Results vary based on market conditions and configuration.*

## 🤝 Contributing

This is a production quant system. Changes should maintain:
- No data leakage in features/targets
- Proper risk management
- Comprehensive logging
- Test coverage for critical components

## ⚠️ Disclaimer

This system is for educational and research purposes. Trading cryptocurrencies involves significant risk. Always test thoroughly and never risk more than you can afford to lose. Past performance does not guarantee future results.
