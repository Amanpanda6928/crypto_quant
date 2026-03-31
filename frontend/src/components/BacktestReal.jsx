import { useState, useEffect, useRef } from "react";
import api from "../api/api";
import { ALL_COINS } from "../services/api";
import { Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';

// All 20 coins for backtest (live from Binance)
const BACKTEST_COINS = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 
  'ADAUSDT', 'AVAXUSDT', 'DOGEUSDT', 'DOTUSDT', 'LINKUSDT',
  'MATICUSDT', 'LTCUSDT', 'BCHUSDT', 'UNIUSDT', 'ATOMUSDT',
  'XLMUSDT', 'ICPUSDT', 'APTUSDT', 'ARBUSDT', 'OPUSDT'
];

// Live intervals up to 1h
const BACKTEST_INTERVALS = [
  { interval: '1m', name: '1 Minute' },
  { interval: '5m', name: '5 Minutes' },
  { interval: '15m', name: '15 Minutes' },
  { interval: '30m', name: '30 Minutes' },
  { interval: '1h', name: '1 Hour' }
];

const PREDICTION_TIMEFRAMES = [
  { value: '15m', label: '15m', desc: 'Short' },
  { value: '30m', label: '30m', desc: 'Medium' },
  { value: '1h', label: '1h', desc: 'Balanced' },
  { value: '4h', label: '4h', desc: 'Low Noise' },
  { value: '1d', label: '1d', desc: 'High Acc' }
];

const BacktestReal = () => {
  const chartRef = useRef(null);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [strategy, setStrategy] = useState('ma_crossover');
  const [interval, setInterval] = useState('1h');
  const [limit, setLimit] = useState(500);
  const [initialBalance, setInitialBalance] = useState(10000);
  const [parameters, setParameters] = useState({});
  const [availableStrategies, setAvailableStrategies] = useState([]);
  const [availableSymbols, setAvailableSymbols] = useState(BACKTEST_COINS.map(c => ({ symbol: c, name: c.replace('USDT', '') })));
  const [availableIntervals, setAvailableIntervals] = useState(BACKTEST_INTERVALS);
  const [comparisonResults, setComparisonResults] = useState([]);
  const [dataSource, setDataSource] = useState('Binance Live');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [predictionTimeframe, setPredictionTimeframe] = useState('1h');
  const [backtestHistory, setBacktestHistory] = useState([]);

  // Fetch available options
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [strategiesRes, symbolsRes, intervalsRes] = await Promise.all([
          api.get('/backtest-real/strategies'),
          api.get('/backtest-real/symbols'),
          api.get('/backtest-real/intervals')
        ]);

        if (strategiesRes.data.success) {
          setAvailableStrategies(strategiesRes.data.strategies);
        }
        if (symbolsRes.data.success) {
          setAvailableSymbols(symbolsRes.data.symbols);
        }
        if (intervalsRes.data.success) {
          setAvailableIntervals(intervalsRes.data.intervals);
        }
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };
    fetchData();
  }, []);

  // Set default parameters based on strategy
  useEffect(() => {
    const strategyConfig = availableStrategies.find(s => s.name === strategy);
    if (strategyConfig) {
      const defaultParams = {};
      Object.entries(strategyConfig.parameters).forEach(([key, config]) => {
        defaultParams[key] = config.default;
      });
      setParameters(defaultParams);
    }
  }, [strategy, availableStrategies]);

  // Auto-refresh backtest every 15 minutes
  useEffect(() => {
    if (!data) return;
    
    const interval = setInterval(() => {
      runDefaultBacktest();
    }, 15 * 60 * 1000); // 15 minutes
    
    return () => clearInterval(interval);
  }, [data, symbol, interval, strategy]);

  // Run single backtest
  const runBacktest = async () => {
    setLoading(true);
    try {
      const requestData = {
        symbol,
        strategy,
        interval,
        limit,
        initial_balance: initialBalance,
        parameters
      };

      const response = await api.post('/backtest-real', requestData);
      
      if (response.data.success) {
        setData(response.data);
        // Add to history - keep only last 10
        setBacktestHistory(prev => {
          const newEntry = {
            id: Date.now(),
            symbol: requestData.symbol,
            strategy: requestData.strategy,
            interval: requestData.interval,
            timestamp: new Date().toLocaleString(),
            result: response.data.result,
            metrics: response.data.metrics,
            signal: response.data.result?.trades?.[0]?.action || 'HOLD'
          };
          return [newEntry, ...prev].slice(0, 10);
        });
      }
    } catch (error) {
      console.error('Backtest error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Run default backtest
  const runDefaultBacktest = async () => {
    setLoading(true);
    try {
      const response = await api.get('/backtest-real');
      
      if (response.data.success) {
        setData(response.data);
        // Add to history
        setBacktestHistory(prev => {
          const newEntry = {
            id: Date.now(),
            symbol: symbol || 'BTCUSDT',
            strategy: strategy || 'ma_crossover',
            interval: interval || '1h',
            timestamp: new Date().toLocaleString(),
            result: response.data.result,
            metrics: response.data.metrics,
            signal: response.data.result?.trades?.[0]?.action || 'HOLD'
          };
          return [newEntry, ...prev].slice(0, 10);
        });
      }
    } catch (error) {
      console.error('Default backtest error:', error);
    } finally {
      setLoading(false);
    }
  };

  // Compare strategies
  const compareStrategies = async () => {
    setLoading(true);
    try {
      const requestData = {
        symbol,
        strategies: ['ma_crossover', 'rsi', 'bollinger_bands', 'macd'],
        interval,
        limit
      };

      const response = await api.post('/backtest-real/compare', requestData);
      
      if (response.data.success) {
        setComparisonResults(response.data.comparison);
      }
    } catch (error) {
      console.error('Comparison error:', error);
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

  return (
    <div className="backtest-container">
      <div className="backtest-header">
        <h3>📈 Real Backtesting Engine</h3>
        <p>Test strategies with real Binance data</p>
      </div>

      <div className="backtest-controls">
        <div className="control-row">
          <div className="control-group">
            <label>Symbol:</label>
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
              {availableSymbols.map((sym) => (
                <option key={sym.symbol} value={sym.symbol}>
                  {sym.name} ({sym.symbol})
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Strategy:</label>
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)}>
              {availableStrategies.map((strat) => (
                <option key={strat.name} value={strat.name}>
                  {strat.display_name}
                </option>
              ))}
            </select>
          </div>

          <div className="control-group">
            <label>Data Points:</label>
            <select value={limit} onChange={(e) => setLimit(parseInt(e.target.value))}>
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={500}>500</option>
              <option value={1000}>1000</option>
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
              {PREDICTION_TIMEFRAMES.map((tf) => (
                <option key={tf.value} value={tf.value}>
                  {tf.label} - {tf.desc}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Strategy Parameters */}
        {Object.keys(parameters).length > 0 && (
          <div className="strategy-params">
            <h4>Strategy Parameters:</h4>
            <div className="params-grid">
              {Object.entries(parameters).map(([paramName, value]) => {
                const paramConfig = availableStrategies
                  .find(s => s.name === strategy)
                  ?.parameters?.[paramName];
                
                return (
                  <div key={paramName} className="param-group">
                    <label>
                      {paramName.replace(/_/g, ' ').toUpperCase()}:
                    </label>
                    {paramConfig?.type === 'float' ? (
                      <input
                        type="number"
                        value={value}
                        onChange={(e) => handleParameterChange(paramName, parseFloat(e.target.value))}
                        min={paramConfig?.min}
                        max={paramConfig?.max}
                        step="0.01"
                      />
                    ) : (
                      <input
                        type="number"
                        value={value}
                        onChange={(e) => handleParameterChange(paramName, parseInt(e.target.value))}
                        min={paramConfig?.min}
                        max={paramConfig?.max}
                      />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="control-buttons">
          <button 
            onClick={runDefaultBacktest} 
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? 'Running...' : 'Run Default Backtest'}
          </button>
          <button 
            onClick={runBacktest} 
            disabled={loading}
            className="btn btn-secondary"
          >
            {loading ? 'Running...' : 'Run Custom Backtest'}
          </button>
          <button 
            onClick={compareStrategies} 
            disabled={loading}
            className="btn btn-info"
          >
            {loading ? 'Comparing...' : 'Compare All Strategies'}
          </button>
        </div>
      </div>

      {/* Results Section */}
      {data && (
        <div className="backtest-results">
          <h4>📊 Backtest Results</h4>
          
          {/* Data Info */}
          <div className="data-info">
            <h5>Data Information:</h5>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Symbol:</span>
                <span className="value">{data.data_info?.symbol}</span>
              </div>
              <div className="info-item">
                <span className="label">Data Points:</span>
                <span className="value">{data.data_info?.data_points}</span>
              </div>
              <div className="info-item">
                <span className="label">Interval:</span>
                <span className="value">{data.data_info?.interval}</span>
              </div>
              <div className="info-item" style={{ display: 'none' }}>
                <span className="label">Data Source:</span>
                <span className={`value ${data.data_info?.mock_data ? 'warning' : 'success'}`}>
                  {data.data_info?.mock_data ? 'Mock Data' : 'Binance Live'}
                </span>
              </div>
              <div className="info-item">
                <span className="label">Prediction TF:</span>
                <span className="value" style={{ color: '#8b5cf6' }}>{predictionTimeframe}</span>
              </div>
            </div>
          </div>

          {/* Performance Metrics */}
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
              <h5>Win Rate</h5>
              <span className="result-value">
                {formatPercentage(data.result?.win_rate || 0)}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Total Trades</h5>
              <span className="result-value">
                {data.result?.total_trades || 0}
              </span>
            </div>
            
            <div className="result-card">
              <h5>Wins / Losses</h5>
              <span className="result-value">
                {data.result?.wins || 0} / {data.result?.losses || 0}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Backtest History - 10 Latest Results */}
      {backtestHistory.length > 0 && (
        <div className="backtest-history" style={{ marginTop: '30px', background: '#f8f9fa', padding: '20px', borderRadius: '8px' }}>
          <h4>📜 Last 10 Backtest Results</h4>
          <div className="history-table" style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
              <thead>
                <tr style={{ background: '#e3f2fd' }}>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>#</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Symbol</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Strategy</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Signal</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Return</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Win Rate</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Trades</th>
                  <th style={{ padding: '10px', textAlign: 'left', borderBottom: '2px solid #ddd' }}>Time</th>
                </tr>
              </thead>
              <tbody>
                {backtestHistory.map((item, index) => (
                  <tr key={item.id} style={{ borderBottom: '1px solid #eee', background: index % 2 === 0 ? 'white' : '#fafafa' }}>
                    <td style={{ padding: '10px' }}>{index + 1}</td>
                    <td style={{ padding: '10px', fontWeight: 'bold' }}>{item.symbol}</td>
                    <td style={{ padding: '10px' }}>{item.strategy}</td>
                    <td style={{ padding: '10px' }}>
                      <span style={{
                        padding: '4px 10px',
                        borderRadius: '4px',
                        fontWeight: 'bold',
                        fontSize: '11px',
                        textTransform: 'uppercase',
                        background: item.signal === 'BUY' ? 'rgba(40,167,69,0.2)' : item.signal === 'SELL' ? 'rgba(220,53,69,0.2)' : 'rgba(255,193,7,0.2)',
                        color: item.signal === 'BUY' ? '#28a745' : item.signal === 'SELL' ? '#dc3545' : '#ffc107',
                        border: `1px solid ${item.signal === 'BUY' ? '#28a745' : item.signal === 'SELL' ? '#dc3545' : '#ffc107'}`
                      }}>
                        {item.signal === 'BUY' ? '🟢 BUY' : item.signal === 'SELL' ? '🔴 SELL' : '🟡 HOLD'}
                      </span>
                    </td>
                    <td style={{ padding: '10px', color: (item.metrics?.total_return || 0) >= 0 ? '#28a745' : '#dc3545', fontWeight: 'bold' }}>
                      {formatPercentage(item.metrics?.total_return || 0)}
                    </td>
                    <td style={{ padding: '10px' }}>{formatPercentage(item.result?.win_rate || 0)}</td>
                    <td style={{ padding: '10px' }}>{item.result?.total_trades || 0}</td>
                    <td style={{ padding: '10px', fontSize: '11px', color: '#666' }}>{item.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Strategy Comparison */}
      {comparisonResults.length > 0 && (
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
                  <th>Trades</th>
                </tr>
              </thead>
              <tbody>
                {comparisonResults.map((result, index) => (
                  <tr key={result.strategy} className={index === 0 ? 'best-strategy' : ''}>
                    <td>{result.strategy}</td>
                    <td className={result.total_return >= 0 ? 'positive' : 'negative'}>
                      {formatPercentage(result.total_return)}
                    </td>
                    <td>{result.sharpe_ratio.toFixed(3)}</td>
                    <td className="negative">{formatPercentage(result.max_drawdown)}</td>
                    <td>{formatPercentage(result.win_rate)}</td>
                    <td>{result.total_trades}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Chart Section */}
      {data?.result?.equity && (
        <div className="chart-container">
          <h4>📈 Equity Curve</h4>
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
            <p>Processing backtest...</p>
          </div>
        </div>
      )}

      <style jsx>{`
        .backtest-container {
          padding: 20px;
          max-width: 1400px;
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

        .control-row {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
          margin-bottom: 20px;
        }

        .control-group {
          display: flex;
          flex-direction: column;
        }

        .control-group label {
          margin-bottom: 5px;
          font-weight: 500;
          color: #555;
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

        .params-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 15px;
        }

        .param-group {
          display: flex;
          flex-direction: column;
        }

        .param-group label {
          margin-bottom: 5px;
          font-size: 12px;
          color: #666;
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

        .btn-info {
          background: #17a2b8;
          color: white;
        }

        .btn:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .data-info {
          background: #e3f2fd;
          padding: 15px;
          border-radius: 4px;
          margin-bottom: 20px;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 10px;
        }

        .info-item {
          display: flex;
          justify-content: space-between;
        }

        .info-item .label {
          font-weight: 500;
          color: #666;
        }

        .info-item .value {
          font-weight: bold;
        }

        .info-item .value.success {
          color: #28a745;
        }

        .info-item .value.warning {
          color: #ffc107;
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

export default BacktestReal;
