import { useState, useEffect, useRef } from "react";
import api from "../api/api";
import { ALL_COINS, fetchBinanceKlines } from "../services/api";
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';

const TIMEFRAMES = [
  { value: '15m', label: '15m', desc: 'Short' },
  { value: '30m', label: '30m', desc: 'Medium' },
  { value: '1h', label: '1h', desc: 'Balanced' },
  { value: '4h', label: '4h', desc: 'Low Noise' },
  { value: '1d', label: '1d', desc: 'High Acc' }
];

const Backtest = () => {
  const chartRef = useRef(null);
  const [equityData, setEquityData] = useState([]);
  const [backtestResult, setBacktestResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [strategy, setStrategy] = useState('ai_signals');
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [initialBalance, setInitialBalance] = useState(10000);
  const [parameters, setParameters] = useState({});
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [interval, setInterval] = useState('1h');
  const [dataSource, setDataSource] = useState('Live Binance');
  const [predictionTimeframe, setPredictionTimeframe] = useState('1h');

  // Fetch available strategies
  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const response = await api.get('/backtest/strategies');
        if (response.data.success) {
          setAvailableStrategies(response.data.strategies);
        }
      } catch (error) {
        console.error('Error fetching strategies:', error);
      }
    };
    fetchStrategies();
  }, []);

  // Auto-refresh backtest every 15 minutes
  useEffect(() => {
    if (!backtestResult) return;
    
    const interval = setInterval(() => {
      runSimpleBacktest();
    }, 15 * 60 * 1000); // 15 minutes
    
    return () => clearInterval(interval);
  }, [symbol, interval, strategy, backtestResult]);

  // Simple backtest function with LIVE data
  const runSimpleBacktest = async () => {
    setLoading(true);
    try {
      // Fetch live klines from Binance
      const klinesData = await fetchBinanceKlines(symbol.replace('USDT', ''), interval, 100);
      
      if (!klinesData || !klinesData.candles || klinesData.candles.length === 0) {
        console.error('No live data available');
        setLoading(false);
        return;
      }
      
      // Extract closing prices from klines
      const prices = klinesData.candles.map(c => c.close);
      
      const response = await api.post('/backtest', { prices });
      
      if (response.data.success) {
        // Format data for chart
        const chartData = response.data.equity.map((value, index) => ({
          time: index,
          value: value,
          date: new Date(klinesData.candles[index]?.time || Date.now() - (100 - index) * 24 * 60 * 60 * 1000).toLocaleDateString()
        }));
        
        setEquityData(chartData);
        setBacktestResult({...response.data, dataSource: 'Live Binance'});
      }
    } catch (error) {
      console.error('Backtest error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Advanced backtest function
  const runAdvancedBacktest = async () => {
    setLoading(true);
    try {
      const requestData = {
        symbol,
        strategy,
        initial_balance: initialBalance,
        parameters,
        start_date: '2024-01-01',
        end_date: '2024-03-01'
      };

      const response = await api.post('/backtest/advanced', requestData);
      
      if (response.data.success) {
        const result = response.data.result;
        
        // Format equity curve data
        const chartData = result.equity_curve.map((value, index) => ({
          time: index,
          value: value,
          date: new Date(Date.now() - (100 - index) * 24 * 60 * 60 * 1000).toLocaleDateString()
        }));
        
        setEquityData(chartData);
        setBacktestResult(result);
      }
    } catch (error) {
      console.error('Advanced backtest error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle parameter changes
  const handleParameterChange = (paramName, value) => {
    setParameters(prev => ({
      ...prev,
      [paramName]: value
    }));
  };

  // Get strategy parameters
  const getStrategyParams = () => {
    const strategyConfig = availableStrategies.find(s => s.name === strategy);
    return strategyConfig?.parameters || {};
  };

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  // Format percentage
  const formatPercentage = (value) => {
    return `${value.toFixed(2)}%`;
  };

  return (
    <div className="backtest-container">
      <div className="backtest-header">
        <h3>📈 Backtesting Engine</h3>
        <p>Test your trading strategies with historical data</p>
      </div>

      <div className="backtest-controls">
        <div className="control-group">
          <label>Symbol:</label>
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {ALL_COINS.map(coin => (
              <option key={coin.symbol} value={`${coin.symbol}USDT`}>
                {coin.symbol}/USDT
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Strategy:</label>
          <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
            {availableStrategies.map((strat) => (
              <option key={strat.name} value={strat.name}>
                {strat.description}
              </option>
            ))}
          </select>
        </div>

        <div className="control-group">
          <label>Initial Balance:</label>
          <input
            type="number"
            value={initialBalance}
            onChange={(e) => setInitialBalance(parseFloat(e.target.value))}
            min="1000"
            max="100000"
            step="1000"
          />
        </div>

        <div className="control-group">
          <label>Prediction TF:</label>
          <select value={predictionTimeframe} onChange={(e) => setPredictionTimeframe(e.target.value)}>
            {TIMEFRAMES.map((tf) => (
              <option key={tf.value} value={tf.value}>
                {tf.label} - {tf.desc}
              </option>
            ))}
          </select>
        </div>

        {/* Strategy Parameters */}
        {Object.keys(getStrategyParams()).length > 0 && (
          <div className="strategy-params">
            <h4>Strategy Parameters:</h4>
            {Object.entries(getStrategyParams()).map(([paramName, config]) => (
              <div key={paramName} className="param-group">
                <label>
                  {paramName.replace(/_/g, ' ').toUpperCase()}:
                </label>
                {config.type === 'float' ? (
                  <input
                    type="number"
                    value={parameters[paramName] || config.default}
                    onChange={(e) => handleParameterChange(paramName, parseFloat(e.target.value))}
                    min={config.min}
                    max={config.max}
                    step="0.01"
                  />
                ) : (
                  <input
                    type="number"
                    value={parameters[paramName] || config.default}
                    onChange={(e) => handleParameterChange(paramName, parseInt(e.target.value))}
                    min={config.min}
                    max={config.max}
                  />
                )}
              </div>
            ))}
          </div>
        )}

        <div className="control-buttons">
          <button 
            onClick={runSimpleBacktest} 
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? 'Running...' : 'Run Simple Backtest'}
          </button>
          <button 
            onClick={runAdvancedBacktest} 
            disabled={loading}
            className="btn btn-secondary"
          >
            {loading ? 'Running...' : 'Run Advanced Backtest'}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {backtestResult && (
        <div className="backtest-results">
          <h4>📊 Backtest Results</h4>
          
          <div className="results-grid">
            <div className="result-card">
              <h5>Initial Balance</h5>
              <span className="result-value">
                {formatCurrency(backtestResult.initial_balance || 10000)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Final Balance</h5>
              <span className="result-value">
                {formatCurrency(backtestResult.final_balance)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Total Return</h5>
              <span className={`result-value ${backtestResult.total_return >= 0 ? 'positive' : 'negative'}`}>
                {formatPercentage(backtestResult.total_return)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Sharpe Ratio</h5>
              <span className="result-value">
                {backtestResult.sharpe_ratio?.toFixed(3) || 'N/A'}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Max Drawdown</h5>
              <span className="result-value negative">
                {formatPercentage(backtestResult.max_drawdown || 0)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Win Rate</h5>
              <span className="result-value">
                {formatPercentage(backtestResult.win_rate || 0)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Total Trades</h5>
              <span className="result-value">
                {backtestResult.total_trades || backtestResult.trades?.length || 0}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Best Trade</h5>
              <span className="result-value positive">
                {formatCurrency(backtestResult.best_trade || 0)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Worst Trade</h5>
              <span className="result-value negative">
                {formatCurrency(backtestResult.worst_trade || 0)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Chart Section */}
      {equityData.length > 0 && (
        <div className="chart-container">
          <h4>📈 Equity Curve</h4>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={equityData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                label="Time"
                tickFormatter={(value) => `Day ${value}`}
              />
              <YAxis 
                label="Portfolio Value ($)"
                tickFormatter={(value) => `$${value.toLocaleString()}`}
              />
              <Tooltip 
                formatter={(value, name) => [
                  formatCurrency(value),
                  'Portfolio Value'
                ]}
                labelFormatter={(label) => `Day ${label}`}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="value" 
                stroke="#8884d8" 
                fill="#8884d8" 
                fillOpacity={0.3}
                strokeWidth={2}
                name="Portfolio Value"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Running backtest...</p>
          </div>
        </div>
      )}

      <style jsx>{`
        .backtest-container {
          padding: 20px;
          max-width: 1200px;
          margin: 0 auto;
        }

        .backtest-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .backtest-header h3 {
          color: #333;
          margin-bottom: 10px;
        }

        .backtest-controls {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 30px;
        }

        .control-group {
          display: inline-block;
          margin-right: 20px;
          margin-bottom: 10px;
        }

        .control-group label {
          display: block;
          margin-bottom: 5px;
          font-weight: 500;
        }

        .control-group input,
        .control-group select {
          padding: 8px 12px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 14px;
        }

        .strategy-params {
          margin-top: 20px;
          padding: 15px;
          background: #e9ecef;
          border-radius: 4px;
        }

        .param-group {
          display: inline-block;
          margin-right: 15px;
          margin-bottom: 10px;
        }

        .param-group label {
          display: block;
          margin-bottom: 5px;
          font-size: 12px;
        }

        .control-buttons {
          margin-top: 20px;
          text-align: center;
        }

        .btn {
          padding: 12px 24px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
          margin: 0 10px;
        }

        .btn-primary {
          background: #007bff;
          color: white;
        }

        .btn-secondary {
          background: #6c757d;
          color: white;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .backtest-results {
          margin-bottom: 30px;
        }

        .results-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-top: 20px;
        }

        .result-card {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          text-align: center;
        }

        .result-card h5 {
          margin: 0 0 10px 0;
          color: #666;
          font-size: 14px;
        }

        .result-value {
          font-size: 18px;
          font-weight: bold;
          color: #333;
        }

        .result-value.positive {
          color: #28a745;
        }

        .result-value.negative {
          color: #dc3545;
        }

        .chart-container {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .loading-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .loading-spinner {
          background: white;
          padding: 30px;
          border-radius: 8px;
          text-align: center;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #007bff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 15px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default Backtest;
