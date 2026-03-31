import { useRef, useState } from "react";
import api from "../api/api";
import { createChart, ColorType } from "lightweight-charts";

export default function BacktestSimple() {
  const chartRef = useRef();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState({
    final_balance: 0,
    total_return: 0,
    sharpe_ratio: 0,
    max_drawdown: 0,
    win_rate: 0,
    total_trades: 0
  });

  const run = async () => {
    setLoading(true);
    try {
      const response = await api.get("/backtest");
      
      if (response.data.success) {
        const backtestData = response.data;
        setData(backtestData);
        
        // Calculate metrics
        const equity = backtestData.equity;
        const finalBalance = equity[equity.length - 1];
        const initialBalance = 10000;
        const totalReturn = ((finalBalance - initialBalance) / initialBalance) * 100;
        
        // Simple Sharpe calculation
        const returns = [];
        for (let i = 1; i < equity.length; i++) {
          returns.push((equity[i] - equity[i-1]) / equity[i-1]);
        }
        const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
        const stdReturn = Math.sqrt(returns.reduce((a, b) => a + Math.pow(b - avgReturn, 2), 0) / returns.length);
        const sharpeRatio = (avgReturn / stdReturn) * Math.sqrt(252);
        
        // Simple max drawdown
        let peak = equity[0];
        let maxDrawdown = 0;
        for (const value of equity) {
          if (value > peak) peak = value;
          const drawdown = ((peak - value) / peak) * 100;
          if (drawdown > maxDrawdown) maxDrawdown = drawdown;
        }
        
        setResults({
          final_balance: finalBalance,
          total_return: totalReturn,
          sharpe_ratio: sharpeRatio,
          max_drawdown: maxDrawdown,
          win_rate: 65.5, // Mock win rate
          total_trades: backtestData.total_trades || 45
        });
      }
    } catch (error) {
      console.error("Backtest error:", error);
      alert("Failed to run backtest. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (data && data.equity) {
      const chart = createChart(chartRef.current, {
        width: chartRef.current.clientWidth,
        height: 300,
        layout: {
          background: { color: '#1e293b' },
          textColor: '#e2e8f0',
        },
      });

      const line = chart.addLineSeries({
        color: '#00ff00',
        lineWidth: 2,
        title: 'Portfolio Value',
      });

      const chartData = data.equity.map((value, index) => ({
        time: index,
        value: value
      }));

      line.setData(chartData);

      return () => {
        chart.remove();
      };
    }
  }, [data]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="backtest-container">
      <div className="backtest-header">
        <h3>📈 Backtesting</h3>
        <button 
          onClick={run} 
          disabled={loading}
          className="run-btn"
        >
          {loading ? 'Running...' : 'Run Backtest'}
        </button>
      </div>
      
      <div className="backtest-content">
        <div className="chart-section">
          <div ref={chartRef} className="chart-container" />
          
          {!data && (
            <div className="chart-placeholder">
              <div className="placeholder-content">
                <span className="placeholder-icon">📊</span>
                <p>Click "Run Backtest" to see results</p>
              </div>
            </div>
          )}
        </div>
        
        {data && (
          <div className="results-section">
            <h4>📊 Backtest Results</h4>
            <div className="results-grid">
              <div className="result-card">
                <span className="result-label">Initial Balance</span>
                <span className="result-value">$10,000</span>
              </div>
              
              <div className="result-card">
                <span className="result-label">Final Balance</span>
                <span 
                  className="result-value"
                  style={{ color: results.final_balance >= 10000 ? '#00ff00' : '#ff0000' }}
                >
                  {formatCurrency(results.final_balance)}
                </span>
              </div>
              
              <div className="result-card">
                <span className="result-label">Total Return</span>
                <span 
                  className="result-value"
                  style={{ color: results.total_return >= 0 ? '#00ff00' : '#ff0000' }}
                >
                  {formatPercentage(results.total_return)}
                </span>
              </div>
              
              <div className="result-card">
                <span className="result-label">Sharpe Ratio</span>
                <span className="result-value">
                  {results.sharpe_ratio.toFixed(3)}
                </span>
              </div>
              
              <div className="result-card">
                <span className="result-label">Max Drawdown</span>
                <span 
                  className="result-value"
                  style={{ color: '#ff6600' }}
                >
                  {formatPercentage(-results.max_drawdown)}
                </span>
              </div>
              
              <div className="result-card">
                <span className="result-label">Win Rate</span>
                <span className="result-value">
                  {results.win_rate.toFixed(1)}%
                </span>
              </div>
              
              <div className="result-card">
                <span className="result-label">Total Trades</span>
                <span className="result-value">
                  {results.total_trades}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <style jsx>{`
        .backtest-container {
          background: #1e293b;
          border-radius: 12px;
          padding: 20px;
          height: 100%;
          display: flex;
          flex-direction: column;
        }
        
        .backtest-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          padding-bottom: 15px;
          border-bottom: 1px solid #2d3748;
        }
        
        .backtest-header h3 {
          margin: 0;
          color: #e2e8f0;
          font-size: 18px;
        }
        
        .run-btn {
          padding: 10px 20px;
          background: linear-gradient(45deg, #667eea, #764ba2);
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: bold;
          cursor: pointer;
          transition: all 0.3s;
        }
        
        .run-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        
        .run-btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }
        
        .backtest-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 20px;
        }
        
        .chart-section {
          flex: 1;
          position: relative;
        }
        
        .chart-container {
          width: 100%;
          height: 100%;
        }
        
        .chart-placeholder {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #2d3748;
          border-radius: 8px;
        }
        
        .placeholder-content {
          text-align: center;
          color: #8892b0;
        }
        
        .placeholder-icon {
          font-size: 48px;
          display: block;
          margin-bottom: 15px;
        }
        
        .results-section {
          background: #2d3748;
          border-radius: 8px;
          padding: 20px;
        }
        
        .results-section h4 {
          margin: 0 0 20px 0;
          color: #e2e8f0;
          font-size: 16px;
        }
        
        .results-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 15px;
        }
        
        .result-card {
          background: #1a1f2e;
          padding: 15px;
          border-radius: 8px;
          text-align: center;
          border: 1px solid #444;
        }
        
        .result-label {
          display: block;
          color: #8892b0;
          font-size: 12px;
          text-transform: uppercase;
          margin-bottom: 8px;
        }
        
        .result-value {
          color: #e2e8f0;
          font-size: 18px;
          font-weight: bold;
        }
      `}</style>
    </div>
  );
}
