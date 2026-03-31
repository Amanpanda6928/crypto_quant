export default function CoinSelector({ setSymbol, currentSymbol }) {
  const coins = [
    { symbol: "BTCUSDT", name: "Bitcoin", icon: "₿" },
    { symbol: "ETHUSDT", name: "Ethereum", icon: "Ξ" },
    { symbol: "BNBUSDT", name: "Binance Coin", icon: "🅱️" },
    { symbol: "ADAUSDT", name: "Cardano", icon: "₳" },
    { symbol: "SOLUSDT", name: "Solana", icon: "◎" },
    { symbol: "DOGEUSDT", name: "Dogecoin", icon: "🐕" },
    { symbol: "DOTUSDT", name: "Polkadot", icon: "●" },
    { symbol: "MATICUSDT", name: "Polygon", icon: "⬟" },
    { symbol: "AVAXUSDT", name: "Avalanche", icon: "🔺" },
    { symbol: "LINKUSDT", name: "Chainlink", icon: "🔗" }
  ];

  return (
    <div className="coin-selector">
      <h3>🪙 Select Coin</h3>
      <div className="coins-grid">
        {coins.map((coin) => (
          <button
            key={coin.symbol}
            onClick={() => setSymbol(coin.symbol)}
            className={`coin-button ${currentSymbol === coin.symbol ? 'active' : ''}`}
          >
            <span className="coin-icon">{coin.icon}</span>
            <span className="coin-name">{coin.name}</span>
            <span className="coin-symbol">{coin.symbol}</span>
          </button>
        ))}
      </div>
      
      <style jsx>{`
        .coin-selector {
          background: #1e293b;
          border-radius: 12px;
          padding: 20px;
        }
        
        .coin-selector h3 {
          margin: 0 0 20px 0;
          color: #e2e8f0;
          font-size: 18px;
        }
        
        .coins-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
          gap: 10px;
        }
        
        .coin-button {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 15px 10px;
          background: #2d3748;
          border: 1px solid #444;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.3s;
        }
        
        .coin-button:hover {
          background: #3a4556;
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        .coin-button.active {
          background: linear-gradient(45deg, #667eea, #764ba2);
          border-color: #667eea;
          box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
        }
        
        .coin-icon {
          font-size: 24px;
        }
        
        .coin-name {
          color: #e2e8f0;
          font-weight: 500;
          font-size: 14px;
        }
        
        .coin-symbol {
          color: #8892b0;
          font-size: 11px;
          font-family: monospace;
        }
        
        .coin-button.active .coin-name {
          color: white;
        }
        
        .coin-button.active .coin-symbol {
          color: rgba(255, 255, 255, 0.8);
        }
      `}</style>
    </div>
  );
}
