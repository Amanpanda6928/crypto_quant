import { useState, useEffect } from "react";
import api from "../api/api";

export default function Trades() {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        const response = await api.get("/trades");
        if (response.data.success) {
          setTrades(response.data.trades);
        } else {
          // Generate mock trades for demo
          const mockTrades = [
            {
              id: 1,
              symbol: "BTCUSDT",
              side: "BUY",
              price: 44500,
              quantity: 0.05,
              total: 2225.00,
              timestamp: "2024-01-15T10:30:00Z",
              status: "FILLED",
              pnl: 125.50,
              pnl_percentage: 5.64
            },
            {
              id: 2,
              symbol: "ETHUSDT",
              side: "SELL",
              price: 3250,
              quantity: 2.0,
              total: 6500.00,
              timestamp: "2024-01-15T11:45:00Z",
              status: "FILLED",
              pnl: -85.00,
              pnl_percentage: -1.31
            },
            {
              id: 3,
              symbol: "ADAUSDT",
              side: "BUY",
              price: 1.20,
              quantity: 1000,
              total: 1200.00,
              timestamp: "2024-01-15T12:15:00Z",
              status: "FILLED",
              pnl: 45.00,
              pnl_percentage: 3.75
            },
            {
              id: 4,
              symbol: "SOLUSDT",
              side: "SELL",
              price: 125.00,
              quantity: 10,
              total: 1250.00,
              timestamp: "2024-01-15T13:20:00Z",
              status: "FILLED",
              pnl: 200.00,
              pnl_percentage: 1.60
            },
            {
              id: 5,
              symbol: "BNBUSDT",
              side: "BUY",
              price: 320,
              quantity: 5,
              total: 1600.00,
              timestamp: "2024-01-15T14:30:00Z",
              status: "PENDING",
              pnl: 0,
              pnl_percentage: 0
            }
          ];
          setTrades(mockTrades);
        }
      } catch (error) {
        console.error("Error fetching trades:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchTrades();
    
    // Update trades every 10 seconds
    const interval = setInterval(() => {
      setTrades(prev => prev.map(trade => ({
        ...trade,
        // Simulate small price changes for pending trades
        pnl: trade.status === "PENDING" ? (Math.random() - 0.5) * 10 : trade.pnl,
        pnl_percentage: trade.status === "PENDING" ? (Math.random() - 0.5) * 0.5 : trade.pnl_percentage
      })));
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  const getSideColor = (side) => {
    return side === 'BUY' ? '#00ff00' : '#ff0000';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'FILLED':
        return '#00ff00';
      case 'PENDING':
        return '#ffa500';
      case 'CANCELLED':
        return '#ff0000';
      default:
        return '#888888';
    }
  };

  const getPnLColor = (pnl) => {
    if (pnl > 0) return '#00ff00';
    if (pnl < 0) return '#ff0000';
    return '#888888';
  };

  if (loading) {
    return (
      <div className="trades-container">
        <h3>📋 Recent Trades</h3>
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading trades...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="trades-container">
      <div className="trades-header">
        <h3>📋 Recent Trades</h3>
        <div className="trade-stats">
          <span className="stat-item">
            Total: {trades.length}
          </span>
          <span className="stat-item">
            P&L: <span style={{ color: trades.reduce((sum, t) => sum + (t.pnl || 0), 0) >= 0 ? '#00ff00' : '#ff0000' }}>
              {formatCurrency(trades.reduce((sum, t) => sum + (t.pnl || 0), 0))}
            </span>
          </span>
        </div>
      </div>
      
      <div className="trades-list">
        {trades.length === 0 ? (
          <div className="no-trades">
            <span className="no-trades-icon">📭</span>
            <p>No trades yet</p>
          </div>
        ) : (
          trades.map((trade, index) => (
            <div key={trade.id || index} className="trade-item">
              <div className="trade-main">
                <div className="trade-symbol">
                  <span className="symbol-text">{trade.symbol}</span>
                  <span 
                    className="trade-side"
                    style={{ color: getSideColor(trade.side) }}
                  >
                    {trade.side}
                  </span>
                </div>
                
                <div className="trade-price">
                  <span className="price-label">Price:</span>
                  <span className="price-value">{formatCurrency(trade.price)}</span>
                </div>
                
                <div className="trade-quantity">
                  <span className="quantity-label">Qty:</span>
                  <span className="quantity-value">{trade.quantity}</span>
                </div>
                
                <div className="trade-total">
                  <span className="total-label">Total:</span>
                  <span className="total-value">{formatCurrency(trade.total)}</span>
                </div>
              </div>
              
              <div className="trade-details">
                <div className="trade-pnl">
                  <span className="pnl-label">P&L:</span>
                  <span 
                    className="pnl-value"
                    style={{ color: getPnLColor(trade.pnl) }}
                  >
                    {formatCurrency(trade.pnl)}
                  </span>
                  <span 
                    className="pnl-percentage"
                    style={{ color: getPnLColor(trade.pnl) }}
                  >
                    ({trade.pnl_percentage >= 0 ? '+' : ''}{trade.pnl_percentage.toFixed(2)}%)
                  </span>
                </div>
                
                <div className="trade-status">
                  <span className="status-label">Status:</span>
                  <span 
                    className="status-value"
                    style={{ color: getStatusColor(trade.status) }}
                  >
                    {trade.status}
                  </span>
                </div>
                
                <div className="trade-time">
                  <span className="time-label">Time:</span>
                  <span className="time-value">{formatTime(trade.timestamp)}</span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
      
      <style jsx>{`
        .trades-container {
          background: #1e293b;
          border-radius: 12px;
          padding: 20px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .trades-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 1px solid #2d3748;
        }
        
        .trades-header h3 {
          margin: 0;
          color: #e2e8f0;
          font-size: 18px;
        }
        
        .trade-stats {
          display: flex;
          gap: 20px;
        }
        
        .stat-item {
          color: #8892b0;
          font-size: 14px;
        }
        
        .loading-spinner {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 200px;
          gap: 20px;
        }
        
        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #667eea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        
        .trades-list {
          flex: 1;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }
        
        .no-trades {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 200px;
          color: #8892b0;
        }
        
        .no-trades-icon {
          font-size: 48px;
          margin-bottom: 15px;
        }
        
        .trade-item {
          background: #2d3748;
          border-radius: 8px;
          padding: 15px;
          border: 1px solid #444;
          transition: all 0.3s;
        }
        
        .trade-item:hover {
          background: #3a4556;
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        .trade-main {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr 1fr;
          gap: 15px;
          margin-bottom: 12px;
        }
        
        .trade-symbol {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        
        .symbol-text {
          color: #e2e8f0;
          font-weight: bold;
          font-size: 16px;
        }
        
        .trade-side {
          font-size: 12px;
          font-weight: bold;
          text-transform: uppercase;
          padding: 2px 6px;
          border-radius: 4px;
        }
        
        .trade-price,
        .trade-quantity,
        .trade-total {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        
        .price-label,
        .quantity-label,
        .total-label {
          color: #8892b0;
          font-size: 11px;
          text-transform: uppercase;
        }
        
        .price-value,
        .quantity-value,
        .total-value {
          color: #e2e8f0;
          font-weight: 500;
          font-size: 14px;
        }
        
        .trade-details {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 15px;
        }
        
        .trade-pnl,
        .trade-status,
        .trade-time {
          display: flex;
          flex-direction: column;
          gap: 5px;
        }
        
        .pnl-label,
        .status-label,
        .time-label {
          color: #8892b0;
          font-size: 11px;
          text-transform: uppercase;
        }
        
        .pnl-value {
          font-weight: bold;
          font-size: 14px;
        }
        
        .pnl-percentage {
          font-size: 12px;
          margin-left: 5px;
        }
        
        .status-value {
          font-weight: bold;
          font-size: 12px;
          text-transform: uppercase;
        }
        
        .time-value {
          color: #e2e8f0;
          font-size: 12px;
        }
      `}</style>
    </div>
  );
}
