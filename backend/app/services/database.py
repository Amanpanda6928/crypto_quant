"""
SQL Server Database Service
Handles all database operations for predictions, backtests, and user data
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pyodbc
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from contextlib import contextmanager

# Database Configuration
DB_CONFIG = {
    'server': os.getenv('DB_SERVER', 'localhost'),
    'database': os.getenv('DB_NAME', 'CryptoQuantDB'),
    'username': os.getenv('DB_USER', 'sa'),
    'password': os.getenv('DB_PASSWORD', 'YourPassword123'),
    'driver': os.getenv('DB_DRIVER', '{ODBC Driver 17 for SQL Server}')
}


class DatabaseService:
    """
    SQL Server database service for Crypto Quant application
    Tables:
    - Predictions: Store AI/technical predictions
    - Backtests: Store backtesting results
    - Signals: Store trading signals history
    - Users: User data and preferences
    """

    def __init__(self):
        self.connection_string = (
            f"DRIVER={DB_CONFIG['driver']};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            f"UID={DB_CONFIG['username']};"
            f"PWD={DB_CONFIG['password']}"
        )
        self._init_database()

    @contextmanager
    def _get_connection(self):
        """Get database connection context manager"""
        conn = None
        try:
            conn = pyodbc.connect(self.connection_string)
            yield conn
        except Exception as e:
            print(f"[Database] Connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _init_database(self):
        """Initialize database tables"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Predictions table
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Predictions' AND xtype='U')
                    CREATE TABLE Predictions (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        coin VARCHAR(10) NOT NULL,
                        timeframe VARCHAR(10) NOT NULL,
                        signal VARCHAR(10) NOT NULL,
                        confidence INT NOT NULL,
                        price DECIMAL(18,8),
                        target DECIMAL(18,8),
                        stop_loss DECIMAL(18,8),
                        rr_ratio DECIMAL(5,2),
                        rsi DECIMAL(5,2),
                        macd DECIMAL(10,4),
                        atr DECIMAL(18,8),
                        factors NVARCHAR(MAX),
                        source VARCHAR(50),
                        created_at DATETIME DEFAULT GETDATE(),
                        updated_at DATETIME DEFAULT GETDATE()
                    )
                """)

                # Backtests table
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Backtests' AND xtype='U')
                    CREATE TABLE Backtests (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        coin VARCHAR(10) NOT NULL,
                        timeframe VARCHAR(20) NOT NULL,
                        total_trades INT,
                        win_rate DECIMAL(5,2),
                        avg_win_pct DECIMAL(8,4),
                        avg_loss_pct DECIMAL(8,4),
                        profit_factor DECIMAL(8,2),
                        max_drawdown DECIMAL(8,2),
                        sharpe_ratio DECIMAL(5,2),
                        total_return DECIMAL(8,2),
                        start_equity DECIMAL(18,2),
                        final_equity DECIMAL(18,2),
                        trades_json NVARCHAR(MAX),
                        created_at DATETIME DEFAULT GETDATE()
                    )
                """)

                # Signals history table
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='SignalHistory' AND xtype='U')
                    CREATE TABLE SignalHistory (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        coin VARCHAR(10) NOT NULL,
                        timeframe VARCHAR(10) NOT NULL,
                        signal VARCHAR(10) NOT NULL,
                        confidence INT,
                        price DECIMAL(18,8),
                        result VARCHAR(10),
                        pnl_pct DECIMAL(8,4),
                        created_at DATETIME DEFAULT GETDATE(),
                        resolved_at DATETIME
                    )
                """)

                # Users table
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
                    CREATE TABLE Users (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        name VARCHAR(100),
                        role VARCHAR(20) DEFAULT 'user',
                        preferences NVARCHAR(MAX),
                        created_at DATETIME DEFAULT GETDATE(),
                        last_login DATETIME
                    )
                """)

                conn.commit()
                print("[Database] Tables initialized successfully")
        except Exception as e:
            print(f"[Database] Init error: {e}")

    def save_prediction(self, coin: str, timeframe: str, prediction: Dict) -> bool:
        """Save a prediction to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Predictions 
                    (coin, timeframe, signal, confidence, price, target, stop_loss, 
                     rr_ratio, rsi, macd, atr, factors, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    coin, timeframe, prediction.get('signal'),
                    prediction.get('confidence', 0),
                    prediction.get('price'), prediction.get('target'),
                    prediction.get('stop'), prediction.get('rr'),
                    prediction.get('rsi'), prediction.get('macd'),
                    prediction.get('atr'),
                    json.dumps(prediction.get('factors', {})),
                    prediction.get('source', 'Finnhub')
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"[Database] Save prediction error: {e}")
            return False

    def get_predictions(self, coin: str = None, timeframe: str = None,
                        limit: int = 100) -> List[Dict]:
        """Get predictions from database"""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM Predictions WHERE 1=1"
                params = []

                if coin:
                    query += " AND coin = ?"
                    params.append(coin)
                if timeframe:
                    query += " AND timeframe = ?"
                    params.append(timeframe)

                query += " ORDER BY created_at DESC OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY"
                params.append(limit)

                df = pd.read_sql(query, conn, params=params)
                return df.to_dict('records')
        except Exception as e:
            print(f"[Database] Get predictions error: {e}")
            return []

    def save_backtest(self, backtest: Dict) -> bool:
        """Save backtest results to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Backtests
                    (coin, timeframe, total_trades, win_rate, avg_win_pct, avg_loss_pct,
                     profit_factor, max_drawdown, sharpe_ratio, total_return,
                     start_equity, final_equity, trades_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    backtest.get('symbol'), backtest.get('timeframe'),
                    backtest.get('total_trades'), backtest.get('win_rate'),
                    backtest.get('avg_win_pct'), backtest.get('avg_loss_pct'),
                    backtest.get('profit_factor'), backtest.get('max_drawdown'),
                    backtest.get('sharpe_ratio'), backtest.get('total_return'),
                    backtest.get('start_equity'), backtest.get('final_equity'),
                    json.dumps(backtest.get('trades', []))
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"[Database] Save backtest error: {e}")
            return False

    def get_backtests(self, coin: str = None, limit: int = 50) -> List[Dict]:
        """Get backtest results from database"""
        try:
            with self._get_connection() as conn:
                query = "SELECT * FROM Backtests WHERE 1=1"
                params = []

                if coin:
                    query += " AND coin = ?"
                    params.append(coin)

                query += " ORDER BY created_at DESC OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY"
                params.append(limit)

                df = pd.read_sql(query, conn, params=params)
                records = df.to_dict('records')

                # Parse trades_json
                for record in records:
                    if 'trades_json' in record and record['trades_json']:
                        record['trades'] = json.loads(record['trades_json'])

                return records
        except Exception as e:
            print(f"[Database] Get backtests error: {e}")
            return []

    def get_top_performers(self, metric: str = 'total_return', limit: int = 10) -> List[Dict]:
        """Get top performing backtests"""
        try:
            with self._get_connection() as conn:
                query = f"""
                    SELECT coin, timeframe, {metric}, win_rate, total_trades, profit_factor
                    FROM Backtests
                    ORDER BY {metric} DESC
                    OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                """
                df = pd.read_sql(query, conn, params=[limit])
                return df.to_dict('records')
        except Exception as e:
            print(f"[Database] Top performers error: {e}")
            return []

    def save_signal_history(self, coin: str, timeframe: str, signal: str,
                            confidence: int, price: float) -> bool:
        """Save signal to history"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO SignalHistory
                    (coin, timeframe, signal, confidence, price)
                    VALUES (?, ?, ?, ?, ?)
                """, (coin, timeframe, signal, confidence, price))
                conn.commit()
                return True
        except Exception as e:
            print(f"[Database] Save signal error: {e}")
            return False

    def get_signal_stats(self, coin: str = None, days: int = 30) -> Dict:
        """Get signal statistics"""
        try:
            with self._get_connection() as conn:
                query = """
                    SELECT 
                        signal,
                        COUNT(*) as count,
                        AVG(confidence) as avg_confidence,
                        AVG(CASE WHEN result = 'WIN' THEN 1 ELSE 0 END) * 100 as win_rate
                    FROM SignalHistory
                    WHERE created_at >= DATEADD(day, -?, GETDATE())
                """
                params = [days]

                if coin:
                    query += " AND coin = ?"
                    params.append(coin)

                query += " GROUP BY signal"

                df = pd.read_sql(query, conn, params=params)
                return df.to_dict('records')
        except Exception as e:
            print(f"[Database] Signal stats error: {e}")
            return []

    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Total predictions
                cursor.execute("SELECT COUNT(*) FROM Predictions")
                total_predictions = cursor.fetchone()[0]

                # Total backtests
                cursor.execute("SELECT COUNT(*) FROM Backtests")
                total_backtests = cursor.fetchone()[0]

                # Total signals
                cursor.execute("SELECT COUNT(*) FROM SignalHistory")
                total_signals = cursor.fetchone()[0]

                # Recent predictions
                df = pd.read_sql("""
                    SELECT TOP 5 coin, signal, confidence, created_at
                    FROM Predictions
                    ORDER BY created_at DESC
                """, conn)

                return {
                    'total_predictions': total_predictions,
                    'total_backtests': total_backtests,
                    'total_signals': total_signals,
                    'recent_predictions': df.to_dict('records')
                }
        except Exception as e:
            print(f"[Database] Dashboard stats error: {e}")
            return {}


# Global instance
_db_service = None


def get_db_service() -> DatabaseService:
    """Get or create database service singleton"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service
