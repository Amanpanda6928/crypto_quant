import { useState } from "react";
import api from "../api/api";

export default function TradeForm({ symbol, currentPrice }) {
  const [side, setSide] = useState("BUY");
  const [quantity, setQuantity] = useState("");
  const [orderType, setOrderType] = useState("MARKET");
  const [limitPrice, setLimitPrice] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const executeTrade = async () => {
    if (!quantity || parseFloat(quantity) <= 0) {
      setMessage("Please enter a valid quantity");
      return;
    }

    if (orderType === "LIMIT" && !limitPrice) {
      setMessage("Please enter a limit price");
      return;
    }

    setLoading(true);
    setMessage("");

    try {
      const tradeData = {
        symbol,
        side,
        quantity: parseFloat(quantity),
        order_type: orderType,
        price: orderType === "LIMIT" ? parseFloat(limitPrice) : currentPrice
      };

      const response = await api.post("/trade", tradeData);
      
      if (response.data.success) {
        setMessage(`✅ ${side} order placed successfully!`);
        setQuantity("");
        setLimitPrice("");
        
        // Clear message after 3 seconds
        setTimeout(() => setMessage(""), 3000);
      } else {
        setMessage(`❌ Order failed: ${response.data.message}`);
      }
    } catch (error) {
      setMessage(`❌ Trade execution failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const calculateTotal = () => {
    const price = orderType === "LIMIT" ? parseFloat(limitPrice) || 0 : currentPrice;
    const qty = parseFloat(quantity) || 0;
    return (price * qty).toFixed(2);
  };

  return (
    <div className="trade-form-container">
      <div className="trade-header">
        <h3>💰 Quick Trade</h3>
        <div className="symbol-info">
          <span className="symbol">{symbol}</span>
          <span className="current-price">
            Current: ${currentPrice.toLocaleString()}
          </span>
        </div>
      </div>

      <div className="trade-form">
        {/* Order Type Selection */}
        <div className="form-row">
          <label className="form-label">Order Type:</label>
          <div className="order-type-selector">
            <button
              className={`order-type-btn ${orderType === "MARKET" ? "active" : ""}`}
              onClick={() => setOrderType("MARKET")}
            >
              Market
            </button>
            <button
              className={`order-type-btn ${orderType === "LIMIT" ? "active" : ""}`}
              onClick={() => setOrderType("LIMIT")}
            >
              Limit
            </button>
          </div>
        </div>

        {/* Side Selection */}
        <div className="form-row">
          <label className="form-label">Side:</label>
          <div className="side-selector">
            <button
              className={`side-btn buy ${side === "BUY" ? "active" : ""}`}
              onClick={() => setSide("BUY")}
            >
              🟢 BUY
            </button>
            <button
              className={`side-btn sell ${side === "SELL" ? "active" : ""}`}
              onClick={() => setSide("SELL")}
            >
              🔴 SELL
            </button>
          </div>
        </div>

        {/* Quantity Input */}
        <div className="form-row">
          <label className="form-label">Quantity:</label>
          <input
            type="number"
            className="quantity-input"
            placeholder="0.00"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            min="0.001"
            step="0.001"
          />
          <span className="quantity-info">
            {symbol.replace("USDT", "")}
          </span>
        </div>

        {/* Limit Price (for LIMIT orders) */}
        {orderType === "LIMIT" && (
          <div className="form-row">
            <label className="form-label">Limit Price:</label>
            <input
              type="number"
              className="price-input"
              placeholder="0.00"
              value={limitPrice}
              onChange={(e) => setLimitPrice(e.target.value)}
              min="0"
              step="0.01"
            />
            <span className="currency">USD</span>
          </div>
        )}

        {/* Total Calculation */}
        <div className="form-row total-row">
          <label className="form-label">Total:</label>
          <span className="total-amount">${calculateTotal()}</span>
        </div>

        {/* Message Display */}
        {message && (
          <div className={`trade-message ${message.includes("✅") ? "success" : "error"}`}>
            {message}
          </div>
        )}

        {/* Execute Button */}
        <button
          onClick={executeTrade}
          disabled={loading}
          className={`execute-btn ${side === "BUY" ? "buy" : "sell"}`}
        >
          {loading ? "Executing..." : `${side} ${orderType}`}
        </button>
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <button
          onClick={() => {
            setQuantity("0.01");
            setSide("BUY");
            setOrderType("MARKET");
          }}
          className="quick-btn"
        >
          Quick Buy 0.01
        </button>
        <button
          onClick={() => {
            setQuantity("0.01");
            setSide("SELL");
            setOrderType("MARKET");
          }}
          className="quick-btn"
        >
          Quick Sell 0.01
        </button>
        <button
          onClick={() => {
            setQuantity("0.1");
            setSide("BUY");
            setOrderType("MARKET");
          }}
          className="quick-btn"
        >
          Buy 0.1
        </button>
        <button
          onClick={() => {
            setQuantity("0.1");
            setSide("SELL");
            setOrderType("MARKET");
          }}
          className="quick-btn"
        >
          Sell 0.1
        </button>
      </div>
      
      <style jsx>{`
        .trade-form-container {
          background: #1e293b;
          border-radius: 8px;
          padding: 20px;
          height: 100%;
        }
        
        .trade-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 1px solid #2d3748;
        }
        
        .trade-header h3 {
          margin: 0;
          color: #e2e8f0;
          font-size: 18px;
        }
        
        .symbol-info {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 5px;
        }
        
        .symbol {
          color: #00ff00;
          font-weight: bold;
          font-size: 16px;
        }
        
        .current-price {
          color: #8892b0;
          font-size: 14px;
        }
        
        .trade-form {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }
        
        .form-row {
          display: flex;
          align-items: center;
          gap: 15px;
        }
        
        .form-label {
          color: #e2e8f0;
          font-weight: 500;
          min-width: 100px;
        }
        
        .order-type-selector,
        .side-selector {
          display: flex;
          gap: 10px;
        }
        
        .order-type-btn,
        .side-btn {
          padding: 8px 16px;
          border: 1px solid #2d3748;
          background: #1a1f2e;
          color: #8892b0;
          border-radius: 6px;
          cursor: pointer;
          transition: all 0.3s;
          font-weight: 500;
        }
        
        .order-type-btn.active,
        .side-btn.active {
          background: #667eea;
          color: white;
          border-color: #667eea;
        }
        
        .side-btn.buy.active {
          background: #00ff00;
          border-color: #00ff00;
        }
        
        .side-btn.sell.active {
          background: #ff0000;
          border-color: #ff0000;
        }
        
        .quantity-input,
        .price-input {
          flex: 1;
          padding: 10px;
          border: 1px solid #2d3748;
          background: #0a0e27;
          color: #e2e8f0;
          border-radius: 6px;
          font-size: 14px;
        }
        
        .quantity-info,
        .currency {
          color: #8892b0;
          font-size: 12px;
          margin-left: 10px;
        }
        
        .total-row {
          background: #2d3748;
          padding: 10px;
          border-radius: 6px;
          margin-top: 5px;
        }
        
        .total-amount {
          color: #00ff00;
          font-size: 18px;
          font-weight: bold;
        }
        
        .trade-message {
          padding: 10px;
          border-radius: 6px;
          text-align: center;
          font-weight: 500;
          margin-top: 10px;
        }
        
        .trade-message.success {
          background: rgba(0, 255, 0, 0.1);
          color: #00ff00;
          border: 1px solid #00ff00;
        }
        
        .trade-message.error {
          background: rgba(255, 0, 0, 0.1);
          color: #ff0000;
          border: 1px solid #ff0000;
        }
        
        .execute-btn {
          padding: 12px 24px;
          border: none;
          border-radius: 8px;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s;
          margin-top: 15px;
        }
        
        .execute-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .execute-btn.buy {
          background: linear-gradient(45deg, #00ff00, #00cc00);
          color: #000;
        }
        
        .execute-btn.sell {
          background: linear-gradient(45deg, #ff0000, #cc0000);
          color: #fff;
        }
        
        .execute-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }
        
        .quick-actions {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 10px;
          margin-top: 20px;
        }
        
        .quick-btn {
          padding: 8px 12px;
          background: #2d3748;
          color: #e2e8f0;
          border: 1px solid #444;
          border-radius: 6px;
          cursor: pointer;
          font-size: 12px;
          transition: all 0.2s;
        }
        
        .quick-btn:hover {
          background: #444;
          transform: translateY(-1px);
        }
      `}</style>
    </div>
  );
}
