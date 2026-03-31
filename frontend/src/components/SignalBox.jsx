import { useState, useEffect } from "react";
import api from "../api/api";

export default function SignalBox() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSignals = async () => {
      try {
        const response = await api.get('/api/live-bot/signals');
        if (response.data.success) {
          setSignals(response.data.signals);
        }
      } catch (error) {
        console.error('Error fetching signals:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSignals();
    const interval = setInterval(fetchSignals, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const getSignalColor = (signal) => {
    switch (signal) {
      case "BUY": return "#00ff00";
      case "STRONG_BUY": return "#00cc00";
      case "SELL": return "#ff0000";
      case "STRONG_SELL": return "#cc0000";
      case "HOLD": return "#ffa500";
      default: return "#888888";
    }
  };

  if (loading) return <div className="signal-loading">Loading AI signals...</div>;

  return (
    <div className="signal-box">
      <div className="signal-header">
        <h3>🔴 LIVE AI Signals</h3>
        <span className="update-time">{new Date().toLocaleTimeString()}</span>
      </div>
      
      <div className="signals-grid">
        {signals.map((signal) => (
          <div 
            key={signal.coin} 
            className="signal-card"
            style={{ borderColor: getSignalColor(signal.signal) }}
          >
            <div className="coin-name">{signal.coin}</div>
            <div className="signal-value" style={{ color: getSignalColor(signal.signal) }}>
              {signal.signal}
            </div>
            <div className="confidence">{Math.round(signal.confidence * 100)}% confidence</div>
            <div className="price">${signal.price?.toLocaleString()}</div>
          </div>
        ))}
      </div>
      
      <style jsx>{`
        .signal-box { background: #1e293b; border-radius: 12px; padding: 20px; height: 100%; }
        .signal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #2d3748; }
        .signal-header h3 { margin: 0; color: #e2e8f0; font-size: 18px; }
        .update-time { color: #8892b0; font-size: 12px; }
        .signals-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; }
        .signal-card { background: #0a0e27; padding: 15px; border-radius: 8px; text-align: center; border: 2px solid; transition: transform 0.2s; }
        .signal-card:hover { transform: translateY(-2px); }
        .coin-name { color: #e2e8f0; font-weight: bold; font-size: 16px; margin-bottom: 8px; }
        .signal-value { font-size: 14px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; }
        .confidence { color: #8892b0; font-size: 12px; margin-bottom: 5px; }
        .price { color: #00ff00; font-size: 14px; font-weight: 500; }
        .signal-loading { color: #8892b0; text-align: center; padding: 40px; }
      `}</style>
    </div>
  );
}
