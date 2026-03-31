import { useState, useEffect } from "react";
import api from "../api/api";

export default function BotControl() {
  const [botStatus, setBotStatus] = useState({
    running: false,
    mode: "PAPER",
    trades_today: 0,
    max_trades: 50,
    daily_pnl: 0,
    last_trade: null,
    uptime: "0h 0m",
    strategy: "AI_FUSION",
    risk_level: "LOW"
  });

  useEffect(() => {
    // Fetch bot status every 5 seconds
    const fetchBotStatus = async () => {
      try {
        const response = await api.get("/live/status");
        if (response.data.success) {
          setBotStatus(response.data.status);
        }
      } catch (error) {
        // Generate mock status for demo
        const mockStatus = {
          running: Math.random() > 0.5,
          mode: "PAPER",
          trades_today: Math.floor(Math.random() * 20),
          max_trades: 50,
          daily_pnl: (Math.random() - 0.5) * 1000,
          last_trade: Math.random() > 0.5 ? new Date().toISOString() : null,
          uptime: `${Math.floor(Math.random() * 5)}h ${Math.floor(Math.random() * 60)}m`,
          strategy: "AI_FUSION",
          risk_level: ["LOW", "MEDIUM", "HIGH"][Math.floor(Math.random() * 3)]
        };
        setBotStatus(mockStatus);
      }
    };

    fetchBotStatus();
    const interval = setInterval(fetchBotStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const startBot = async () => {
    try {
      const response = await api.post("/live/start");
      if (response.data.success) {
        setBotStatus(prev => ({ ...prev, running: true }));
        alert("🚀 Bot started successfully!");
      } else {
        alert(`❌ Failed to start bot: ${response.data.message}`);
      }
    } catch (error) {
      alert(`❌ Error starting bot: ${error.message}`);
    }
  };

  const stopBot = async () => {
    try {
      const response = await api.post("/live/stop");
      if (response.data.success) {
        setBotStatus(prev => ({ ...prev, running: false }));
        alert("🛑 Bot stopped successfully!");
      } else {
        alert(`❌ Failed to stop bot: ${response.data.message}`);
      }
    } catch (error) {
      alert(`❌ Error stopping bot: ${error.message}`);
    }
  };

  const emergencyStop = async () => {
    if (window.confirm("⚠️ This will close all positions and stop the bot. Are you sure?")) {
      try {
        const response = await api.post("/live/emergency-stop");
        if (response.data.success) {
          setBotStatus(prev => ({ ...prev, running: false }));
          alert("🚨 Emergency stop executed!");
        } else {
          alert(`❌ Emergency stop failed: ${response.data.message}`);
        }
      } catch (error) {
        alert(`❌ Error executing emergency stop: ${error.message}`);
      }
    }
  };

  const getRiskLevelColor = (level) => {
    switch (level) {
      case "LOW":
        return "#00ff00";
      case "MEDIUM":
        return "#ffa500";
      case "HIGH":
        return "#ff6600";
      case "CRITICAL":
        return "#ff0000";
      default:
        return "#888888";
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  return (
    <div className="bot-control-container">
      <div className="bot-header">
        <h3>🤖 Bot Control</h3>
        <div className={`status-indicator ${botStatus.running ? 'running' : 'stopped'}`}>
          <span className="status-dot"></span>
          <span className="status-text">
            {botStatus.running ? 'RUNNING' : 'STOPPED'}
          </span>
        </div>
      </div>
      
      <div className="bot-info">
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Mode:</span>
            <span className="info-value">{botStatus.mode}</span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Strategy:</span>
            <span className="info-value">{botStatus.strategy}</span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Trades Today:</span>
            <span className="info-value">
              {botStatus.trades_today}/{botStatus.max_trades}
            </span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Daily P&L:</span>
            <span 
              className="info-value"
              style={{ color: botStatus.daily_pnl >= 0 ? '#00ff00' : '#ff0000' }}
            >
              {formatCurrency(botStatus.daily_pnl)}
            </span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Uptime:</span>
            <span className="info-value">{botStatus.uptime}</span>
          </div>
          
          <div className="info-item">
            <span className="info-label">Risk Level:</span>
            <span 
              className="info-value risk-level"
              style={{ color: getRiskLevelColor(botStatus.risk_level) }}
            >
              {botStatus.risk_level}
            </span>
          </div>
        </div>
      </div>
      
      <div className="bot-controls">
        <button
          onClick={startBot}
          disabled={botStatus.running}
          className="control-btn start-btn"
        >
          🚀 Start Bot
        </button>
        
        <button
          onClick={stopBot}
          disabled={!botStatus.running}
          className="control-btn stop-btn"
        >
          🛑 Stop Bot
        </button>
        
        <button
          onClick={emergencyStop}
          className="control-btn emergency-btn"
        >
          🚨 Emergency Stop
        </button>
      </div>
      
      <div className="bot-stats">
        <div className="stat-item">
          <span className="stat-label">Last Trade:</span>
          <span className="stat-value">
            {botStatus.last_trade 
              ? new Date(botStatus.last_trade).toLocaleString()
              : 'No trades today'
            }
          </span>
        </div>
        
        <div className="progress-bar">
          <span className="progress-label">Daily Trade Limit:</span>
          <div className="progress-track">
            <div 
              className="progress-fill"
              style={{ 
                width: `${(botStatus.trades_today / botStatus.max_trades) * 100}%`,
                backgroundColor: (botStatus.trades_today / botStatus.max_trades) > 0.8 ? '#ff6600' : '#00ff00'
              }}
            ></div>
          </div>
          <span className="progress-text">
            {Math.round((botStatus.trades_today / botStatus.max_trades) * 100)}%
          </span>
        </div>
      </div>
      
      <style jsx>{`
        .bot-control-container {
          background: #1e293b;
          border-radius: 12px;
          padding: 20px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .bot-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 1px solid #2d3748;
        }
        
        .bot-header h3 {
          margin: 0;
          color: #e2e8f0;
          font-size: 18px;
        }
        
        .status-indicator {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 6px 12px;
          border-radius: 20px;
          font-weight: 500;
          font-size: 12px;
        }
        
        .status-indicator.running {
          background: rgba(0, 255, 0, 0.2);
          color: #00ff00;
          border: 1px solid #00ff00;
        }
        
        .status-indicator.stopped {
          background: rgba(255, 0, 0, 0.2);
          color: #ff0000;
          border: 1px solid #ff0000;
        }
        
        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: currentColor;
          animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        
        .bot-info {
          flex: 1;
          margin-bottom: 20px;
        }
        
        .info-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 15px;
        }
        
        .info-item {
          display: flex;
          flex-direction: column;
          background: #2d3748;
          padding: 12px;
          border-radius: 8px;
        }
        
        .info-label {
          color: #8892b0;
          font-size: 12px;
          text-transform: uppercase;
          margin-bottom: 4px;
        }
        
        .info-value {
          color: #e2e8f0;
          font-size: 14px;
          font-weight: 500;
        }
        
        .risk-level {
          font-weight: bold;
          text-transform: uppercase;
        }
        
        .bot-controls {
          display: flex;
          gap: 10px;
          margin-bottom: 20px;
        }
        
        .control-btn {
          flex: 1;
          padding: 12px;
          border: none;
          border-radius: 8px;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s;
          font-size: 14px;
        }
        
        .control-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        
        .start-btn {
          background: linear-gradient(45deg, #00ff00, #00cc00);
          color: #000;
        }
        
        .start-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0, 255, 0, 0.3);
        }
        
        .stop-btn {
          background: linear-gradient(45deg, #ff0000, #cc0000);
          color: #fff;
        }
        
        .stop-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(255, 0, 0, 0.3);
        }
        
        .emergency-btn {
          background: linear-gradient(45deg, #ff6600, #cc5200);
          color: #fff;
        }
        
        .emergency-btn:hover {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(255, 102, 0, 0.3);
        }
        
        .bot-stats {
          background: #2d3748;
          border-radius: 8px;
          padding: 15px;
        }
        
        .stat-item {
          margin-bottom: 15px;
        }
        
        .stat-label {
          color: #8892b0;
          font-size: 12px;
          text-transform: uppercase;
          display: block;
          margin-bottom: 5px;
        }
        
        .stat-value {
          color: #e2e8f0;
          font-size: 13px;
        }
        
        .progress-bar {
          display: flex;
          align-items: center;
          gap: 10px;
        }
        
        .progress-label {
          color: #8892b0;
          font-size: 12px;
          min-width: 120px;
        }
        
        .progress-track {
          flex: 1;
          height: 8px;
          background: #444;
          border-radius: 4px;
          overflow: hidden;
        }
        
        .progress-fill {
          height: 100%;
          transition: width 0.5s ease;
        }
        
        .progress-text {
          color: #e2e8f0;
          font-size: 12px;
          font-weight: bold;
          min-width: 40px;
        }
      `}</style>
    </div>
  );
}
