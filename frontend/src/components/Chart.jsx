import { useEffect, useRef, useState } from "react";
import { createChart, ColorType } from "lightweight-charts";

export default function Chart({ symbol }) {
  const chartRef = useRef();
  const [currentPrice, setCurrentPrice] = useState(0);
  const [priceChange, setPriceChange] = useState(0);

  useEffect(() => {
    const chart = createChart(chartRef.current, {
      width: chartRef.current.clientWidth,
      height: 400,
      layout: {
        background: { type: ColorType.Solid, color: '#0a0e27' },
        textColor: '#e2e8f0',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#1e293b' },
      timeScale: { borderColor: '#1e293b', timeVisible: true },
    });

    const candlestick = chart.addCandlestickSeries({
      upColor: '#00ff00', downColor: '#ff0000',
      borderVisible: false,
      wickUpColor: '#00ff00', wickDownColor: '#ff0000',
    });

    // LIVE BINANCE WEBSOCKET
    const wsUrl = `wss://stream.binance.com:9443/ws/${symbol.toLowerCase()}@kline_1m`;
    const ws = new WebSocket(wsUrl);
    const candleData = [];
    
    ws.onopen = () => console.log(`✅ LIVE: ${symbol} connected`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      const k = data.k;
      
      if (k.x) {
        const candle = {
          time: k.t / 1000,
          open: parseFloat(k.o), high: parseFloat(k.h),
          low: parseFloat(k.l), close: parseFloat(k.c),
        };
        candleData.push(candle);
        if (candleData.length > 100) candleData.shift();
        candlestick.setData(candleData);
        
        const price = parseFloat(k.c);
        const open = parseFloat(k.o);
        const change = ((price - open) / open) * 100;
        setCurrentPrice(price);
        setPriceChange(change);
      }
    };

    const handleResize = () => chart.applyOptions({ width: chartRef.current.clientWidth });
    window.addEventListener('resize', handleResize);

    return () => { ws.close(); window.removeEventListener('resize', handleResize); chart.remove(); };
  }, [symbol]);

  return (
    <div className="chart-wrapper">
      <div className="chart-header">
        <div className="price-display">
          <span className="symbol">{symbol}</span>
          <span className={`price ${priceChange >= 0 ? 'up' : 'down'}`}>
            ${currentPrice.toLocaleString()}
          </span>
          <span className={`change ${priceChange >= 0 ? 'up' : 'down'}`}>
            {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
          </span>
        </div>
        <div className="live-indicator">🔴 LIVE</div>
      </div>
      <div ref={chartRef} className="chart-container" />
      
      <style jsx>{`
        .chart-wrapper { position: relative; width: 100%; height: 100%; background: #0a0e27; border-radius: 12px; overflow: hidden; }
        .chart-header { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: #1e293b; border-bottom: 1px solid #2d3748; }
        .price-display { display: flex; align-items: center; gap: 15px; }
        .symbol { color: #e2e8f0; font-weight: bold; font-size: 18px; }
        .price { font-size: 24px; font-weight: bold; }
        .price.up { color: #00ff00; } .price.down { color: #ff0000; }
        .change { font-size: 14px; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
        .change.up { color: #00ff00; background: rgba(0, 255, 0, 0.1); }
        .change.down { color: #ff0000; background: rgba(255, 0, 0, 0.1); }
        .live-indicator { color: #ff0000; font-size: 12px; font-weight: bold; animation: pulse 1s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .chart-container { width: 100%; height: calc(100% - 70px); }
      `}</style>
    </div>
  );
}
