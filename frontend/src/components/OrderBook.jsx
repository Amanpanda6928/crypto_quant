import { useEffect, useState } from "react";

export default function OrderBook({ symbol }) {
  const [orderBook, setOrderBook] = useState({ bids: [], asks: [] });

  useEffect(() => {
    // Generate mock order book data
    const generateMockOrderBook = () => {
      const bids = [];
      const asks = [];
      let basePrice = 45000;
      
      // Generate bids (buy orders)
      for (let i = 0; i < 10; i++) {
        const price = basePrice - (i + 1) * 10;
        const quantity = Math.random() * 10 + 0.1;
        bids.push({ price, quantity, total: price * quantity });
      }
      
      // Generate asks (sell orders)
      for (let i = 0; i < 10; i++) {
        const price = basePrice + (i + 1) * 10;
        const quantity = Math.random() * 10 + 0.1;
        asks.push({ price, quantity, total: price * quantity });
      }
      
      return { bids: bids.reverse(), asks: asks }; // Reverse bids to show highest first
    };

    // Update order book every 2 seconds
    const interval = setInterval(() => {
      setOrderBook(generateMockOrderBook());
    }, 2000);

    return () => clearInterval(interval);
  }, [symbol]);

  const calculateSpread = () => {
    if (orderBook.bids.length > 0 && orderBook.asks.length > 0) {
      const bestBid = orderBook.bids[0].price;
      const bestAsk = orderBook.asks[0].price;
      return bestAsk - bestBid;
    }
    return 0;
  };

  const calculateTotalVolume = (orders) => {
    return orders.reduce((total, order) => total + order.quantity, 0).toFixed(2);
  };

  return (
    <div className="orderbook-container">
      <div className="orderbook-header">
        <h3>📊 Order Book</h3>
        <div className="spread-info">
          <span className="spread">
            Spread: ${calculateSpread().toFixed(2)}
          </span>
          <span className="symbol">{symbol}</span>
        </div>
      </div>
      
      <div className="orderbook-content">
        <div className="orders-column bids">
          <div className="column-header">
            <span className="header-title">Bids</span>
            <span className="volume">Total: {calculateTotalVolume(orderBook.bids)}</span>
          </div>
          
          <div className="orders-list">
            {orderBook.bids.slice(0, 8).map((bid, index) => (
              <div key={index} className="order-row bid">
                <span className="price">${bid.price.toFixed(2)}</span>
                <span className="quantity">{bid.quantity.toFixed(4)}</span>
                <span className="total">${bid.total.toFixed(0)}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="spread-indicator">
          <div className="spread-line"></div>
          <div className="spread-value">
            {calculateSpread() > 0 ? (
              <span className="spread-amount">${calculateSpread().toFixed(2)}</span>
            ) : (
              <span className="no-spread">--</span>
            )}
          </div>
        </div>
        
        <div className="orders-column asks">
          <div className="column-header">
            <span className="header-title">Asks</span>
            <span className="volume">Total: {calculateTotalVolume(orderBook.asks)}</span>
          </div>
          
          <div className="orders-list">
            {orderBook.asks.slice(0, 8).map((ask, index) => (
              <div key={index} className="order-row ask">
                <span className="price">${ask.price.toFixed(2)}</span>
                <span className="quantity">{ask.quantity.toFixed(4)}</span>
                <span className="total">${ask.total.toFixed(0)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
      
      <style jsx>{`
        .orderbook-container {
          background: #1e293b;
          border-radius: 8px;
          padding: 15px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .orderbook-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 15px;
          padding-bottom: 10px;
          border-bottom: 1px solid #2d3748;
        }
        
        .orderbook-header h3 {
          margin: 0;
          color: #e2e8f0;
          font-size: 16px;
        }
        
        .spread-info {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 2px;
        }
        
        .spread {
          color: #00ff00;
          font-weight: bold;
          font-size: 14px;
        }
        
        .symbol {
          color: #8892b0;
          font-size: 12px;
        }
        
        .orderbook-content {
          flex: 1;
          display: flex;
          gap: 10px;
        }
        
        .orders-column {
          flex: 1;
          display: flex;
          flex-direction: column;
        }
        
        .column-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
          padding-bottom: 5px;
          border-bottom: 1px solid #2d3748;
        }
        
        .header-title {
          color: #e2e8f0;
          font-weight: bold;
          font-size: 14px;
        }
        
        .volume {
          color: #8892b0;
          font-size: 12px;
        }
        
        .orders-list {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }
        
        .order-row {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr;
          gap: 8px;
          padding: 6px 8px;
          border-radius: 4px;
          font-size: 12px;
          transition: background-color 0.2s;
        }
        
        .order-row.bid {
          background: rgba(0, 255, 0, 0.1);
          border-left: 3px solid #00ff00;
        }
        
        .order-row.ask {
          background: rgba(255, 0, 0, 0.1);
          border-left: 3px solid #ff0000;
        }
        
        .order-row:hover {
          background: rgba(255, 255, 255, 0.1);
        }
        
        .order-row span {
          text-align: right;
        }
        
        .price {
          color: #e2e8f0;
          font-weight: 500;
        }
        
        .quantity {
          color: #8892b0;
        }
        
        .total {
          color: #e2e8f0;
          font-weight: bold;
        }
        
        .spread-indicator {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          width: 60px;
          gap: 5px;
        }
        
        .spread-line {
          width: 2px;
          height: 20px;
          background: #2d3748;
        }
        
        .spread-value {
          color: #e2e8f0;
          font-size: 12px;
          font-weight: bold;
          text-align: center;
        }
        
        .spread-amount {
          color: #00ff00;
        }
        
        .no-spread {
          color: #8892b0;
        }
      `}</style>
    </div>
  );
}
