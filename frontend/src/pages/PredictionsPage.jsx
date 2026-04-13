import React, { useState, useEffect } from 'react';
import { PredictionList, TopSignalsList } from '../components/PredictionCard';
import { TimeframeGrid } from '../components/TimeframeBreakdown';
import { 
  getDashboardDataExcel, 
  getAllPredictionsExcel,
  getTopSignalsExcel,
  reloadExcelData,
  generatePredictions 
} from '../api/excelApi';
import { getLivePredictions, getTopSignals as getLiveTopSignals } from '../api/livePredictionsApi';

/**
 * PredictionsPage - Full page for viewing all predictions with percentages
 */
// All 10 supported coins with colors
const ALL_10_COINS = [
  { symbol: 'BTC', name: 'Bitcoin', color: '#f7931a' },
  { symbol: 'ETH', name: 'Ethereum', color: '#627eea' },
  { symbol: 'BNB', name: 'Binance Coin', color: '#f3ba2f' },
  { symbol: 'SOL', name: 'Solana', color: '#9945ff' },
  { symbol: 'XRP', name: 'Ripple', color: '#00aae4' },
  { symbol: 'ADA', name: 'Cardano', color: '#0033ad' },
  { symbol: 'AVAX', name: 'Avalanche', color: '#e84142' },
  { symbol: 'DOGE', name: 'Dogecoin', color: '#c2a633' },
  { symbol: 'DOT', name: 'Polkadot', color: '#e6007a' },
  { symbol: 'LINK', name: 'Chainlink', color: '#2a5ada' }
];

const PredictionsPage = () => {
  const [predictions, setPredictions] = useState([]);
  const [predictionsMap, setPredictionsMap] = useState({});
  const [topSignals, setTopSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('ALL'); // ALL, BUY, SELL
  const [minConfidence, setMinConfidence] = useState(60);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedCoin, setSelectedCoin] = useState(null);
  const [predictionsData, setPredictionsData] = useState({ coins_tracked: 10, total_predictions: 50 });

  useEffect(() => {
    loadAllPredictions();
  }, [filter, minConfidence]);

  const loadAllPredictions = async () => {
    setLoading(true);
    setError(null);
    try {
      // Load from live predictions API
      const [allPredictions, topSignalsData] = await Promise.all([
        getLivePredictions(),
        getLiveTopSignals(minConfidence, 20)
      ]);

      console.log('API Response:', allPredictions);
      
      // Store full API response in state
      setPredictionsData(allPredictions);

      // Handle live prediction format - data comes as { predictions: { COIN: { predictions: { 15m: {...}, 30m: {...} } } } }
      const predictionsMapRaw = allPredictions.predictions || {};
      
      // Extract predictions for each coin
      const predictionsArray = [];
      const predMap = {};
      
      Object.entries(predictionsMapRaw).forEach(([coin, data]) => {
        // The data structure is { predictions: { '15m': {...}, '30m': {...}, '1h': {...}, '4h': {...}, '1d': {...} } }
        const coinData = data.predictions || data;
        
        // Get the 1h prediction as primary, or fall back to first available
        let primary = coinData['1h'];
        if (!primary) {
          // Try other timeframes
          const timeframes = ['15m', '30m', '4h', '1d'];
          for (const tf of timeframes) {
            if (coinData[tf]) {
              primary = coinData[tf];
              break;
            }
          }
        }
        
        if (primary && primary.signal) {
          const formatted = {
            coin: primary.coin || coin,
            signal: primary.signal,
            confidence: primary.confidence || 0,
            price: primary.current_price || primary.price || 0,
            predicted_price: primary.predicted_price || 0,
            price_change: primary.price_change || 0,
            direction: primary.direction || 'NEUTRAL',
            timeframe: primary.timeframe || '1h',
            allTimeframes: coinData
          };
          predictionsArray.push(formatted);
          predMap[coin] = formatted;
        }
      });
      
      console.log('Processed predictions:', predictionsArray);
      
      // Filter by signal type if needed
      let filtered = predictionsArray;
      if (filter !== 'ALL') {
        filtered = predictionsArray.filter(p => p.signal === filter);
      }
      
      // Filter by confidence
      filtered = filtered.filter(p => p.confidence >= minConfidence);

      setPredictions(filtered);
      setPredictionsMap(predMap);
      
      // Load top signals separately
      try {
        const topSignalsData = await getTopSignalsExcel(minConfidence, 20, filter !== 'ALL' ? filter : null);
        setTopSignals(topSignalsData.signals || []);
      } catch (e) {
        console.warn('Could not load top signals:', e);
        setTopSignals([]);
      }
      
      setLastUpdated(allPredictions.last_updated || allPredictions.timestamp);
    } catch (err) {
      console.error('Load error:', err);
      setError('Failed to load predictions: ' + (err.message || 'Unknown error'));
    } finally {
      setLoading(false);
    }
  };

  const handleReload = async () => {
    try {
      await reloadExcelData();
      await loadAllPredictions();
    } catch (err) {
      setError('Reload failed: ' + err.message);
    }
  };

  const handleGenerate = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await generatePredictions();
      console.log('Generated:', result);
      await loadAllPredictions();
    } catch (err) {
      setError('Generation failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Calculate statistics
  const stats = {
    total: predictions.length,
    buy: predictions.filter(p => p.signal === 'BUY').length,
    sell: predictions.filter(p => p.signal === 'SELL').length,
    hold: predictions.filter(p => p.signal === 'HOLD').length,
    avgConfidence: predictions.length > 0 
      ? (predictions.reduce((sum, p) => sum + parseFloat(p.confidence), 0) / predictions.length).toFixed(1)
      : 0
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      {/* Header */}
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">📊 AI Predictions</h1>
            <p className="text-gray-400">
              Real-time trading signals with confidence percentages
              {lastUpdated && (
                <span className="ml-2">
                  • Updated: <span className="text-blue-400">{new Date(lastUpdated).toLocaleTimeString()}</span>
                  <span className="text-xs ml-2 text-gray-500">
                    (Next: {new Date(new Date(lastUpdated).getTime() + 15*60000).toLocaleTimeString()}) • Auto-refresh: 15min
                  </span>
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-2 mt-4 md:mt-0">
            <button
              onClick={handleGenerate}
              disabled={loading}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg font-semibold transition-colors flex items-center gap-2"
            >
              {loading ? '⏳' : '🔮'} Generate Live Predictions
            </button>
            <button
              onClick={handleReload}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors"
            >
              🔄
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-900 border border-red-600 rounded-lg text-red-200">
            {error}
          </div>
        )}

        {/* Stats Cards */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
          <div className="bg-gray-800 p-4 rounded-lg text-center">
            <div className="text-2xl font-bold text-white">{predictionsData.coins_tracked || 10}</div>
            <div className="text-sm text-gray-400">Coins Tracked</div>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg text-center">
            <div className="text-2xl font-bold text-white">{stats.total}</div>
            <div className="text-sm text-gray-400">Total Signals</div>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg text-center">
            <div className="text-2xl font-bold text-green-400">{stats.buy}</div>
            <div className="text-sm text-gray-400">Buy Signals</div>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg text-center">
            <div className="text-2xl font-bold text-red-400">{stats.sell}</div>
            <div className="text-sm text-gray-400">Sell Signals</div>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg text-center">
            <div className="text-2xl font-bold text-yellow-400">{stats.hold}</div>
            <div className="text-sm text-gray-400">Hold Signals</div>
          </div>
          <div className="bg-gray-800 p-4 rounded-lg text-center">
            <div className="text-2xl font-bold text-blue-400">{stats.avgConfidence}%</div>
            <div className="text-sm text-gray-400">Avg Confidence</div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-8 p-4 bg-gray-800 rounded-lg">
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Signal Type:</span>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="px-3 py-2 bg-gray-700 rounded text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
            >
              <option value="ALL">All Signals</option>
              <option value="BUY">Buy Only</option>
              <option value="SELL">Sell Only</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-gray-400">Min Confidence:</span>
            <select
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
              className="px-3 py-2 bg-gray-700 rounded text-white border border-gray-600 focus:border-blue-500 focus:outline-none"
            >
              <option value={0}>Any</option>
              <option value={60}>60%+</option>
              <option value={70}>70%+</option>
              <option value={80}>80%+</option>
              <option value={90}>90%+</option>
            </select>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
            <p className="mt-2 text-gray-400">Loading predictions...</p>
          </div>
        )}

        {/* Content */}
        {!loading && (
          <div className="space-y-8">
            {/* 10 Coins Grid */}
            <div className="mb-8">
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                🪙 10 Cryptocurrencies
              </h2>
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                {ALL_10_COINS.map((coin) => {
                  const prediction = predictionsMap[coin.symbol];
                  const hasData = !!prediction;
                  const signal = prediction?.signal;
                  const confidence = prediction?.confidence;
                  
                  return (
                    <div
                      key={coin.symbol}
                      onClick={() => setSelectedCoin(coin.symbol)}
                      className={`p-3 rounded-lg cursor-pointer transition-all hover:scale-105 ${
                        hasData 
                          ? signal === 'BUY' 
                            ? 'bg-gradient-to-br from-green-900 to-green-800 border border-green-600'
                            : signal === 'SELL'
                              ? 'bg-gradient-to-br from-red-900 to-red-800 border border-red-600'
                              : 'bg-gradient-to-br from-gray-800 to-gray-700 border border-gray-600'
                          : 'bg-gray-800 border border-gray-700 opacity-50'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <div 
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: coin.color }}
                        />
                        <span className="font-bold text-lg">{coin.symbol}</span>
                      </div>
                      <div className="text-xs text-gray-400 truncate">{coin.name}</div>
                      {hasData ? (
                        <div className="mt-2">
                          <div className={`text-sm font-bold ${
                            signal === 'BUY' ? 'text-green-400' : 
                            signal === 'SELL' ? 'text-red-400' : 'text-gray-400'
                          }`}>
                            {signal}
                          </div>
                          <div className="text-xs text-gray-300">
                            {confidence}%
                          </div>
                        </div>
                      ) : (
                        <div className="mt-2 text-xs text-gray-500">No data</div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Selected Coin Detail */}
            {selectedCoin && predictionsMap[selectedCoin] && (
              <div className="p-4 bg-gray-800 rounded-lg border border-blue-600">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-2xl font-bold">{selectedCoin} Details</h3>
                    <p className="text-gray-400">
                      {ALL_10_COINS.find(c => c.symbol === selectedCoin)?.name}
                    </p>
                  </div>
                  <button 
                    onClick={() => setSelectedCoin(null)}
                    className="text-gray-400 hover:text-white"
                  >
                    ✕
                  </button>
                </div>
                
                {/* Prediction Metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                  <div className="p-3 bg-gray-700 rounded">
                    <div className="text-xs text-gray-400">Signal</div>
                    <div className={`text-xl font-bold ${
                      predictionsMap[selectedCoin].signal === 'BUY' ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {predictionsMap[selectedCoin].signal}
                    </div>
                  </div>
                  <div className="p-3 bg-gray-700 rounded">
                    <div className="text-xs text-gray-400">Confidence</div>
                    <div className="text-xl font-bold text-blue-400">
                      {predictionsMap[selectedCoin].confidence}%
                    </div>
                  </div>
                  <div className="p-3 bg-gray-700 rounded">
                    <div className="text-xs text-gray-400">Price Change</div>
                    <div className={`text-xl font-bold ${
                      predictionsMap[selectedCoin].price_change > 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {predictionsMap[selectedCoin].price_change > 0 ? '+' : ''}
                      {predictionsMap[selectedCoin].price_change}%
                    </div>
                  </div>
                  <div className="p-3 bg-gray-700 rounded">
                    <div className="text-xs text-gray-400">Current Price</div>
                    <div className="text-xl font-bold text-white">
                      ${predictionsMap[selectedCoin].price?.toLocaleString()}
                    </div>
                  </div>
                </div>

              </div>
            )}

            {/* Timeframe Signals by Coin */}
            <div className="mb-8">
              <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
                ⏰ Timeframe Signals by Coin
                <span className="text-sm font-normal text-gray-400">(All 5 timeframes)</span>
              </h2>
              <div className="overflow-x-auto">
                <table className="w-full bg-gray-800 rounded-lg overflow-hidden">
                  <thead>
                    <tr className="bg-gray-700 text-gray-300 text-sm">
                      <th className="p-3 text-left font-semibold">Coin</th>
                      <th className="p-3 text-center font-semibold">15m</th>
                      <th className="p-3 text-center font-semibold">30m</th>
                      <th className="p-3 text-center font-semibold">1h</th>
                      <th className="p-3 text-center font-semibold">4h</th>
                      <th className="p-3 text-center font-semibold">1d</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {ALL_10_COINS.map((coin) => {
                      const coinData = predictionsMap[coin.symbol];
                      const timeframes = coinData?.allTimeframes || {};
                      
                      return (
                        <tr key={coin.symbol} className="border-t border-gray-700 hover:bg-gray-750">
                          <td className="p-3">
                            <div className="flex items-center gap-2">
                              <div 
                                className="w-3 h-3 rounded-full"
                                style={{ backgroundColor: coin.color }}
                              />
                              <span className="font-bold">{coin.symbol}</span>
                              <span className="text-gray-500 text-xs">{coin.name}</span>
                            </div>
                          </td>
                          {['15m', '30m', '1h', '4h', '1d'].map((tf) => {
                            const tfData = timeframes[tf];
                            const signal = tfData?.signal || 'HOLD';
                            const confidence = tfData?.confidence || 0;
                            
                            return (
                              <td key={tf} className="p-3 text-center">
                                <div className={`inline-flex flex-col items-center px-2 py-1 rounded ${
                                  signal === 'BUY' ? 'bg-green-900/50' : 
                                  signal === 'SELL' ? 'bg-red-900/50' : 'bg-gray-700/50'
                                }`}>
                                  <span className={`text-xs font-bold ${
                                    signal === 'BUY' ? 'text-green-400' : 
                                    signal === 'SELL' ? 'text-red-400' : 'text-gray-400'
                                  }`}>
                                    {signal}
                                  </span>
                                  <span className="text-[10px] text-gray-400">{confidence}%</span>
                                </div>
                              </td>
                            );
                          })}
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Timeframe Breakdown - UP/DOWN by Time */}
            {predictions.length > 0 && (
              <TimeframeGrid predictions={predictions} />
            )}

            {/* Top Signals Section */}
            {topSignals.length > 0 && (
              <TopSignalsList signals={topSignals.slice(0, 10)} />
            )}

            {/* All Predictions */}
            <PredictionList 
              predictions={predictions} 
              title={`${filter === 'ALL' ? 'All' : filter} Predictions (${predictions.length})`}
            />

            {/* Empty State */}
            {predictions.length === 0 && !loading && (
              <div className="text-center py-12 bg-gray-800 rounded-lg">
                <div className="text-6xl mb-4">📭</div>
                <h3 className="text-xl font-semibold text-gray-300">No predictions found</h3>
                <p className="text-gray-400 mt-2">
                  Try adjusting your filters or reload the data
                </p>
              </div>
            )}
          </div>
        )}

        {/* Info Footer */}
        <div className="mt-12 p-4 bg-gray-800 rounded-lg text-sm text-gray-400">
          <h4 className="font-semibold text-gray-300 mb-2">📈 About Predictions</h4>
          <ul className="space-y-1 list-disc list-inside">
            <li><strong className="text-green-400">BUY</strong>: Price expected to increase (+2% to +5%)</li>
            <li><strong className="text-red-400">SELL</strong>: Price expected to decrease (-1% to -3%)</li>
            <li><strong className="text-yellow-400">Confidence</strong>: Probability of prediction being correct (60-95%)</li>
            <li>Data sourced from: <code className="bg-gray-700 px-1 rounded">crypto_predictions_sample.xlsx</code></li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default PredictionsPage;
