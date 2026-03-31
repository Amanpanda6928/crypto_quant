import { useState, useEffect } from "react";
import api from "../api/api";

export default function PNL({ currentPrice }) {
  const [pnl, setPnl] = useState({
    total: 0,
    daily: 0,
    positions: [],
    lastUpdate: null
  });

  useEffect(() => {
    // Mock PnL data - in real app, fetch from API
    const fetchPNL = async () => {
      try {
        const response = await api.get("/pnl");
        if (response.data.success) {
          setPnl(response.data);
        }
      } catch (error) {
        // Generate mock data for demo
        const mockPNL = {
          total: 1250.75,
          daily: 85.50,
          positions: [
            {
              symbol: "BTCUSDT",
              side: "LONG",
              entry_price: 44500,
              current_price: currentPrice,
              quantity: 0.05,
              pnl: (currentPrice - 44500) * 0.05,
              pnl_percentage: ((currentPrice - 44500) / 44500) * 100,
              entry_time: "2024-01-15T10:30:00Z"
            },
            {
              symbol: "ETHUSDT",
              side: "LONG",
              entry_price: 3200,
              current_price: 3250,
              quantity: 2.0,
              pnl: (3250 - 3200) * 2.0,
              pnl_percentage: ((3250 - 3200) / 3200) * 100,
              entry_time: "2024-01-15T11:45:00Z"
            },
            {
              symbol: "ADAUSDT",
              side: "SHORT",
              entry_price: 1.25,
              current_price: 1.20,
              quantity: 1000,
              pnl: (1.25 - 1.20) * 1000,
              pnl_percentage: ((1.25 - 1.20) / 1.25) * 100,
              entry_time: "2024-01-15T12:15:00Z"
            }
          ],
          lastUpdate: new Date().toISOString()
        };
        setPnl(mockPNL);
      }
    };

    fetchPNL();
    
    // Update PnL every 5 seconds
    const interval = setInterval(() => {
      setPnl(prev => ({
        ...prev,
        positions: prev.positions.map(pos => ({
          ...pos,
          current_price: currentPrice,
          pnl: pos.side === "LONG" 
            ? (currentPrice - pos.entry_price) * pos.quantity
            : (pos.entry_price - currentPrice) * pos.quantity,
          pnl_percentage: pos.side === "LONG"
            ? ((currentPrice - pos.entry_price) / pos.entry_price) * 100
            : ((pos.entry_price - currentPrice) / pos.entry_price) * 100
        })),
        lastUpdate: new Date().toISOString()
      }));
    }, 5000);

    return () => clearInterval(interval);
  }, [currentPrice]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  const totalPnLColor = pnl.total >= 0 ? '#00ff00' : '#ff0000';
  const dailyPnLColor = pnl.daily >= 0 ? '#00ff00' : '#ff0000';

  return (
    <div className="pnl-container">
      <div className="pnl-header">
        <h3>📊 P&L Performance</h3>
        <div className="last-update">
          Last: {pnl.lastUpdate ? new Date(pnl.lastUpdate).toLocaleTimeString() : 'N/A'}
        </div>
      </div>
      
      <div className="pnl-summary">
        <div className="summary-card total">
          <div className="summary-label">Total P&L</div>
          <div className="summary-value" style={{ color: totalPnLColor }}>
            {formatCurrency(pnl.total)}
          </div>
          <div className="summary-change" style={{ color: totalPnLColor }}>
            {pnl.total >= 0 ? '📈' : '📉'} {formatPercentage((pnl.total / 10000) * 100)}
          </div>
        </div>
        
        <div className="summary-card daily">
          <div className="summary-label">Daily P&L</div>
          <div className="summary-value" style={{ color: dailyPnLColor }}>
            {formatCurrency(pnl.daily)}
          </div>
          <div className="summary-change" style={{ color: dailyPnLColor }}>
            {pnl.daily >= 0 ? '📈' : '📉'} {formatPercentage((pnl.daily / 10000) * 100)}
          </div>
        </div>
      </div>
      
      <div className="positions-section">
        <h4>Open Positions</h4>
        <div className="positions-list">
          {pnl.positions.map((position, index) => (
            <div key={index} className="position-card">
              <div className="position-header">
                <span className="position-symbol">{position.symbol}</span>
                <span className={`position-side ${position.side.toLowerCase()}`}>
                  {position.side}
                </span>
              </div>
              
              <div className="position-details">
                <div className="detail-row">
                  <span className="detail-label">Entry:</span>
                  <span className="detail-value">{formatCurrency(position.entry_price)}</span>
                </div>
                
                <div className="detail-row">
                  <span className="detail-label">Current:</span>
                  <span className="detail-value">{formatCurrency(position.current_price)}</span>
                </div>
                
                <div className="detail-row">
                  <span className="detail-label">Quantity:</span>
                  <span className="detail-value">{position.quantity}</span>
                </div>
                
                <div className="detail-row">
                  <span className="detail-label">P&L:</span>
                  <span 
                    className="detail-value pnl-value"
                    style={{ color: position.pnl >= 0 ? '#00ff00' : '#ff0000' }}
                  >
                    {formatCurrency(position.pnl)}
                  </span>
                  <span 
                    className="pnl-percentage"
                    style={{ color: position.pnl >= 0 ? '#00ff00' : '#ff0000' }}
                  >
                    {formatPercentage(position.pnl_percentage)}
                  </span>
                </div>
                
                <div className="detail-row">
                  <span className="detail-label">Entry:</span>
                  <span className="entry-time">
                    {new Date(position.entry_time).toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      
      <style jsx>{`
        .pnl-container {
          background: #1e293b;
          border-radius: 12px;
          padding: 20px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .pnl-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 1px solid #2d3748;
        }
        
        .pnl-header h3 {
          margin: 0;
          color: #e2e8f0;
          font-size: 18px;
        }
        
        .last-update {
          color: #8892b0;
          font-size: 12px;
        }
        
        .pnl-summary {
          display: flex;
          gap: 20px;
          margin-bottom: 20px;
        }
        
        .summary-card {
          flex: 1;
          background: #2d3748;
          padding: 15px;
          border-radius: 8px;
          text-align: center;
        }
        
        .summary-label {
          color: #8892b0;
          font-size: 12px;
          text-transform: uppercase;
          margin-bottom: 8px;
        }
        
        .summary-value {
          font-size: 24px;
          font-weight: bold;
          margin-bottom: 5px;
        }
        
        .summary-change {
          font-size: 14px;
          font-weight: 500;
        }
        
        .positions-section h4 {
          margin: 0 0 15px 0;
          color: #e2e8f0;
          font-size: 16px;
        }
        
        .positions-list {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }
        
        .position-card {
          background: #2d3748;
          border-radius: 8px;
          padding: 15px;
          border: 1px solid #444;
        }
        
        .position-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
        }
        
        .position-symbol {
          color: #e2e8f0;
          font-weight: bold;
          font-size: 16px;
        }
        
        .position-side {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: bold;
          text-transform: uppercase;
        }
        
        .position-side.long {
          background: rgba(0, 255, 0, 0.2);
          color: #00ff00;
        }
        
        .position-side.short {
          background: rgba(255, 0, 0, 0.2);
          color: #ff0000;
        }
        
        .position-details {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 10px;
        }
        
        .detail-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .detail-label {
          color: #8892b0;
          font-size: 12px;
        }
        
        .detail-value {
          color: #e2e8f0;
          font-weight: 500;
        }
        
        .pnl-value {
          font-weight: bold;
          font-size: 16px;
        }
        
        .pnl-percentage {
          font-size: 12px;
          margin-left: 10px;
        }
        
        .entry-time {
          color: #8892b0;
          font-size: 11px;
        }
      `}</style>
    </div>
  );
}
