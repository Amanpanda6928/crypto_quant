import React, { useState, useEffect } from 'react';
import { getDetailedPredictionExcel } from '../api/excelApi';

/**
 * TimeframeBreakdown Component
 * Shows UP/DOWN percentages for each timeframe (15m, 30m, 1h, 4h, 1d)
 */
const TimeframeBreakdown = ({ coin, coinData }) => {
  const [detailedData, setDetailedData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (coin) {
      loadDetailedData();
    }
  }, [coin]);

  const loadDetailedData = async () => {
    setLoading(true);
    try {
      const data = await getDetailedPredictionExcel(coin);
      setDetailedData(data);
    } catch (err) {
      console.error('Error loading detailed data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Timeframe order
  const timeframes = ['15m', '30m', '1h', '4h', '1d'];
  
  // Get prediction for each timeframe
  const getTimeframeData = (tf) => {
    if (!detailedData?.timeframe_predictions) return null;
    return detailedData.timeframe_predictions[tf];
  };

  if (loading) {
    return (
      <div className="p-4 bg-gray-800 rounded-lg animate-pulse">
        <div className="h-4 bg-gray-700 rounded w-1/3 mb-2"></div>
        <div className="h-8 bg-gray-700 rounded"></div>
      </div>
    );
  }

  // If we have coinData (from all_predictions), use that
  const predictions = detailedData?.all_predictions || 
    (coinData ? [coinData] : []);

  if (!predictions || predictions.length === 0) {
    return (
      <div className="p-4 bg-gray-800 rounded-lg text-gray-400">
        No timeframe data available for {coin}
      </div>
    );
  }

  // Group by timeframe
  const byTimeframe = {};
  predictions.forEach(p => {
    const tf = p.Timeframe || p.timeframe;
    if (tf) {
      byTimeframe[tf] = p;
    }
  });

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="p-3 bg-gray-700 border-b border-gray-600">
        <h4 className="font-bold text-white flex items-center gap-2">
          📈 Price Change by Timeframe - {coin}
        </h4>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-0">
        {timeframes.map((tf) => {
          const data = byTimeframe[tf];
          const hasData = !!data;
          const change = data?.Change_Percent || data?.price_change || 0;
          const signal = data?.Signal || data?.signal;
          const confidence = data?.Confidence_Percent || data?.confidence || 0;
          const isUp = change > 0;
          
          return (
            <div 
              key={tf}
              className={`p-4 border-r border-b border-gray-700 last:border-r-0 ${
                hasData 
                  ? isUp 
                    ? 'bg-gradient-to-br from-green-900/30 to-transparent'
                    : 'bg-gradient-to-br from-red-900/30 to-transparent'
                  : 'bg-gray-800/50'
              }`}
            >
              <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">
                {tf}
              </div>
              
              {hasData ? (
                <>
                  <div className={`text-2xl font-bold ${
                    isUp ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {isUp ? '📈' : '📉'} {change > 0 ? '+' : ''}{change.toFixed(2)}%
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${
                      signal === 'BUY' 
                        ? 'bg-green-600 text-white' 
                        : signal === 'SELL'
                          ? 'bg-red-600 text-white'
                          : 'bg-gray-600 text-gray-300'
                    }`}>
                      {signal}
                    </span>
                    <span className="text-xs text-gray-400">
                      {confidence}%
                    </span>
                  </div>
                </>
              ) : (
                <div className="text-gray-500 text-sm">No data</div>
              )}
            </div>
          );
        })}
      </div>
      
      {/* Summary Row */}
      <div className="p-3 bg-gray-700/50 border-t border-gray-600">
        <div className="flex flex-wrap gap-4 text-sm">
          <span className="text-gray-400">
            <strong className="text-white">{predictions.length}</strong> timeframes analyzed
          </span>
          <span className="text-green-400">
            📈 <strong>{predictions.filter(p => (p.Change_Percent || p.price_change) > 0).length}</strong> UP signals
          </span>
          <span className="text-red-400">
            📉 <strong>{predictions.filter(p => (p.Change_Percent || p.price_change) < 0).length}</strong> DOWN signals
          </span>
          <span className="text-blue-400">
            Avg Confidence: <strong>
              {(predictions.reduce((sum, p) => sum + (p.Confidence_Percent || p.confidence || 0), 0) / predictions.length).toFixed(1)}%
            </strong>
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * TimeframeGrid Component
 * Shows all coins with their timeframe breakdown
 */
export const TimeframeGrid = ({ predictions }) => {
  const [selectedCoin, setSelectedCoin] = useState(null);

  // Group predictions by coin
  const byCoin = {};
  predictions.forEach(p => {
    const coin = p.coin || p.Coin;
    if (!byCoin[coin]) {
      byCoin[coin] = [];
    }
    byCoin[coin].push(p);
  });

  // Get best prediction for each coin (highest confidence)
  const coinSummaries = Object.entries(byCoin).map(([coin, preds]) => {
    const best = preds.reduce((max, p) => {
      const conf = p.confidence || p.Confidence_Percent || 0;
      const maxConf = max.confidence || max.Confidence_Percent || 0;
      return conf > maxConf ? p : max;
    }, preds[0]);
    
    return {
      coin,
      predictions: preds,
      best,
      upCount: preds.filter(p => (p.price_change || p.Change_Percent) > 0).length,
      downCount: preds.filter(p => (p.price_change || p.Change_Percent) < 0).length
    };
  });

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white">⏱️ Price Changes by Timeframe</h3>
      
      {/* Coin Selector */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
        {coinSummaries.map(({ coin, best, upCount, downCount }) => {
          const change = best.price_change || best.Change_Percent || 0;
          const signal = best.signal || best.Signal;
          const isUp = change > 0;
          
          return (
            <button
              key={coin}
              onClick={() => setSelectedCoin(selectedCoin === coin ? null : coin)}
              className={`p-3 rounded-lg text-left transition-all hover:scale-105 ${
                selectedCoin === coin
                  ? 'ring-2 ring-blue-500 bg-gray-700'
                  : isUp
                    ? 'bg-gradient-to-br from-green-900/50 to-green-800/30 border border-green-700'
                    : 'bg-gradient-to-br from-red-900/50 to-red-800/30 border border-red-700'
              }`}
            >
              <div className="flex justify-between items-start">
                <span className="font-bold text-lg">{coin}</span>
                <span className="text-xs">
                  {upCount > downCount ? '📈' : '📉'}
                </span>
              </div>
              <div className={`text-xl font-bold ${isUp ? 'text-green-400' : 'text-red-400'}`}>
                {isUp ? '+' : ''}{change.toFixed(2)}%
              </div>
              <div className="text-xs text-gray-400 mt-1">
                {signal} • {upCount}📈 {downCount}📉
              </div>
            </button>
          );
        })}
      </div>

      {/* Detailed Breakdown */}
      {selectedCoin && (
        <div className="mt-6">
          <TimeframeBreakdown 
            coin={selectedCoin} 
            coinData={byCoin[selectedCoin]} 
          />
        </div>
      )}
    </div>
  );
};

export default TimeframeBreakdown;
