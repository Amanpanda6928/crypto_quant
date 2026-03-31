import { useRef, useState, useEffect } from "react";
import api from "../api/api";
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart, BarChart, Bar } from 'recharts';

const Portfolio = () => {
  const chartRef = useRef(null);
  const [data, setData] = useState(null);
  const [optimization, setOptimization] = useState(null);
  const [loading, setLoading] = useState(false);
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [strategies, setStrategies] = useState(['sma', 'rsi', 'bollinger']);
  const [weights, setWeights] = useState({});
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [comparison, setComparison] = useState([]);

  // Fetch available strategies
  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const response = await api.get('/portfolio/strategies');
        if (response.data.success) {
          setAvailableStrategies(response.data.strategies);
        }
      } catch (error) {
        console.error('Error fetching strategies:', error);
      }
    };
    fetchStrategies();
  }, []);

  // Run portfolio backtest
  const runPortfolio = async () => {
    setLoading(true);
    try {
      const response = await api.get('/portfolio/backtest');
      
      if (response.data.success) {
        setData(response.data);
      }
    } catch (error) {
      console.error('Portfolio backtest error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Run custom portfolio backtest
  const runCustomPortfolio = async () => {
    setLoading(true);
    try {
      const requestData = {
        symbol,
        strategies,
        weights: Object.keys(weights).length > 0 ? weights : null,
        interval: '1h',
        limit: 500
      };

      const response = await api.post('/portfolio/backtest', requestData);
      
      if (response.data.success) {
        setData(response.data);
      }
    } catch (error) {
      console.error('Custom portfolio error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Optimize portfolio weights
  const optimizePortfolio = async () => {
    setLoading(true);
    try {
      const requestData = {
        symbol,
        strategies,
        method: 'grid',
        iterations: 1000
      };

      const response = await api.post('/portfolio/optimize', requestData);
      
      if (response.data.success) {
        setOptimization(response.data.result);
        setWeights(response.data.result.best_weights);
      }
    } catch (error) {
      console.error('Optimization error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Monte Carlo optimization
  const runMonteCarlo = async () => {
    setLoading(true);
    try {
      const requestData = {
        symbol,
        strategies,
        method: 'monte_carlo',
        iterations: 5000
      };

      const response = await api.post('/portfolio/optimize', requestData);
      
      if (response.data.success) {
        setOptimization(response.data.result);
        setWeights(response.data.result.best_weights);
      }
    } catch (error) {
      console.error('Monte Carlo error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Compare strategies
  const compareStrategies = async () => {
    setLoading(true);
    try {
      const response = await api.get('/portfolio/comparison');
      
      if (response.data.success) {
        setComparison(response.data.comparison);
      }
    } catch (error) {
      console.error('Comparison error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle strategy selection
  const handleStrategyToggle = (strategy) => {
    setStrategies(prev => 
      prev.includes(strategy) 
        ? prev.filter(s => s !== strategy)
        : [...prev, strategy]
    );
  };

  // Handle weight changes
  const handleWeightChange = (strategy, value) => {
    setWeights(prev => ({
      ...prev,
      [strategy]: parseFloat(value)
    }));
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

  // Prepare chart data
  const getChartData = () => {
    if (!data?.result?.equity) return [];
    
    return data.result.equity.map((value, index) => ({
      time: index,
      value: value,
      date: new Date(Date.now() - (data.result.equity.length - index) * 60 * 60 * 1000).toLocaleDateString()
    }));
  };

  // Get weight distribution chart data
  const getWeightData = () => {
    if (!optimization?.best_weights) return [];
    
    return Object.entries(optimization.best_weights).map(([strategy, weight]) => ({
      strategy: strategy.toUpperCase(),
      weight: weight * 100
    }));
  };

  return (
    <div className="portfolio-container">
      <div className="portfolio-header">
        <h3>📊 Portfolio Optimization</h3>
        <p>Multi-strategy portfolio optimization with advanced analytics</p>
      </div>

      <div className="portfolio-controls">
        <div className="control-section">
          <h4>Portfolio Configuration</h4>
          
          <div className="control-row">
            <div className="control-group">
              <label>Symbol:</label>
              <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
                <option value="BTCUSDT">BTC/USDT</option>
                <option value="ETHUSDT">ETH/USDT</option>
                <option value="ADAUSDT">ADA/USDT</option>
                <option value="SOLUSDT">SOL/USDT</option>
              </select>
            </div>
          </div>

          <div className="control-row">
            <div className="control-group">
              <label>Strategies:</label>
              <div className="strategy-grid">
                {availableStrategies.map((strategy) => (
                  <div key={strategy.name} className="strategy-item">
                    <input
                      type="checkbox"
                      id={strategy.name}
                      checked={strategies.includes(strategy.name)}
                      onChange={() => handleStrategyToggle(strategy.name)}
                    />
                    <label htmlFor={strategy.name}>
                      {strategy.display_name}
                      <span className="strategy-type">{strategy.type}</span>
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {optimization?.best_weights && (
            <div className="control-row">
              <div className="control-group">
                <label>Strategy Weights:</label>
                <div className="weights-grid">
                  {Object.entries(optimization.best_weights).map(([strategy, weight]) => (
                    <div key={strategy} className="weight-item">
                      <label>{strategy.toUpperCase()}:</label>
                      <input
                        type="number"
                        value={weight}
                        onChange={(e) => handleWeightChange(strategy, e.target.value)}
                        min="0"
                        max="1"
                        step="0.01"
                      />
                      <span className="weight-percent">{formatPercentage(weight * 100)}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="control-buttons">
          <button onClick={runPortfolio} disabled={loading} className="btn btn-primary">
            {loading ? 'Running...' : 'Run Default Portfolio'}
          </button>
          <button onClick={runCustomPortfolio} disabled={loading} className="btn btn-secondary">
            {loading ? 'Running...' : 'Run Custom Portfolio'}
          </button>
          <button onClick={optimizePortfolio} disabled={loading} className="btn btn-success">
            {loading ? 'Optimizing...' : 'Grid Optimization'}
          </button>
          <button onClick={runMonteCarlo} disabled={loading} className="btn btn-info">
            {loading ? 'Running...' : 'Monte Carlo'}
          </button>
          <button onClick={compareStrategies} disabled={loading} className="btn btn-warning">
            {loading ? 'Comparing...' : 'Compare Strategies'}
          </button>
        </div>
      </div>

      {/* Optimization Results */}
      {optimization && (
        <div className="optimization-results">
          <h4>🎯 Optimization Results</h4>
          
          <div className="results-grid">
            <div className="result-card">
              <h5>Best Balance</h5>
              <span className="result-value">
                {formatCurrency(optimization.best_balance)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Best Return</h5>
              <span className="result-value positive">
                {formatPercentage((optimization.best_balance - 10000) / 10000 * 100)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Combinations Tested</h5>
              <span className="result-value">
                {optimization.total_combinations_tested || optimization.iterations}
              </span>
            </div>
          </div>

          {/* Weight Distribution Chart */}
          {getWeightData().length > 0 && (
            <div className="weight-chart">
              <h5>Optimal Weight Distribution</h5>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={getWeightData()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="strategy" />
                  <YAxis label="Weight (%)" />
                  <Tooltip formatter={(value) => [`${value.toFixed(1)}%`, 'Weight']} />
                  <Bar dataKey="weight" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Portfolio Results */}
      {data && (
        <div className="portfolio-results">
          <h4>📈 Portfolio Performance</h4>
          
          <div className="results-grid">
            <div className="result-card">
              <h5>Initial Balance</h5>
              <span className="result-value">
                {formatCurrency(data.request?.initial_balance || 10000)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Final Balance</h5>
              <span className={`result-value ${data.result?.final_balance >= 10000 ? 'positive' : 'negative'}`}>
                {formatCurrency(data.result?.final_balance)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Total Return</h5>
              <span className={`result-value ${data.metrics?.total_return >= 0 ? 'positive' : 'negative'}`}>
                {formatPercentage(data.metrics?.total_return || 0)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Sharpe Ratio</h5>
              <span className="result-value">
                {data.metrics?.sharpe_ratio?.toFixed(3) || 'N/A'}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Max Drawdown</h5>
              <span className="result-value negative">
                {formatPercentage(data.metrics?.max_drawdown || 0)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Volatility</h5>
              <span className="result-value">
                {formatPercentage(data.metrics?.volatility || 0)}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Strategy Comparison */}
      {comparison.length > 0 && (
        <div className="comparison-results">
          <h4>🏆 Strategy Comparison</h4>
          <div className="comparison-table">
            <table>
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Return</th>
                  <th>Sharpe</th>
                  <th>Max DD</th>
                  <th>Win Rate</th>
                </tr>
              </thead>
              <tbody>
                {comparison.map((result, index) => (
                  <tr key={result.strategy} className={index === 0 ? 'best-strategy' : ''}>
                    <td>{result.strategy.toUpperCase()}</td>
                    <td className={result.total_return >= 0 ? 'positive' : 'negative'}>
                      {formatPercentage(result.total_return)}
                    </td>
                    <td>{result.sharpe_ratio.toFixed(3)}</td>
                    <td className="negative">{formatPercentage(result.max_drawdown)}</td>
                    <td>{formatPercentage(result.win_rate)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Portfolio Equity Chart */}
      {data?.result?.equity && (
        <div className="chart-container">
          <h4>📊 Portfolio Equity Curve</h4>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={getChartData()}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="time" 
                label="Time"
                tickFormatter={(value) => `T${value}`}
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
                labelFormatter={(label) => `Time ${label}`}
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
            <p>Processing portfolio optimization...</p>
          </div>
        </div>
      )}

      <style jsx>{`
        .portfolio-container {
          padding: 20px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .portfolio-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .portfolio-header h3 {
          color: #333;
          margin-bottom: 10px;
        }

        .portfolio-controls {
          background: #f8f9fa;
          padding: 20px;
          border-radius: 8px;
          margin-bottom: 30px;
        }

        .control-section h4 {
          margin-bottom: 15px;
          color: #495057;
        }

        .control-row {
          margin-bottom: 20px;
        }

        .strategy-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 10px;
        }

        .strategy-item {
          display: flex;
          align-items: center;
          padding: 10px;
          background: white;
          border-radius: 4px;
          border: 1px solid #ddd;
        }

        .strategy-item input {
          margin-right: 10px;
        }

        .strategy-item label {
          display: flex;
          flex-direction: column;
          cursor: pointer;
        }

        .strategy-type {
          font-size: 12px;
          color: #666;
          margin-top: 2px;
        }

        .weights-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 10px;
        }

        .weight-item {
          display: flex;
          flex-direction: column;
          padding: 10px;
          background: white;
          border-radius: 4px;
          border: 1px solid #ddd;
        }

        .weight-item label {
          font-weight: 500;
          margin-bottom: 5px;
        }

        .weight-item input {
          margin-bottom: 5px;
          padding: 5px;
          border: 1px solid #ddd;
          border-radius: 3px;
        }

        .weight-percent {
          font-size: 12px;
          color: #666;
        }

        .control-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 10px;
          margin-top: 20px;
        }

        .btn {
          padding: 12px 20px;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 14px;
        }

        .btn-primary { background: #007bff; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn-info { background: #17a2b8; color: white; }
        .btn-warning { background: #ffc107; color: black; }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }

        .optimization-results {
          background: #e3f2fd;
          padding: 20px;
          border-radius: 8px;
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

        .result-value.positive { color: #28a745; }
        .result-value.negative { color: #dc3545; }

        .weight-chart {
          margin-top: 20px;
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .comparison-results {
          margin-top: 30px;
        }

        .comparison-table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 15px;
        }

        .comparison-table th,
        .comparison-table td {
          padding: 12px;
          text-align: center;
          border: 1px solid #ddd;
        }

        .comparison-table th {
          background: #f8f9fa;
          font-weight: bold;
        }

        .best-strategy {
          background: #d4edda;
          font-weight: bold;
        }

        .chart-container {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          margin-top: 30px;
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

export default Portfolio;
