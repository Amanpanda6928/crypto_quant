import React from 'react';

/**
 * PredictionCard Component
 * Displays a single prediction with proper percentage formatting
 */
const PredictionCard = ({ prediction, detailed = false }) => {
  if (!prediction) return null;

  const {
    coin,
    signal,
    confidence,
    confidence_display,
    price,
    predicted_price,
    price_change,
    price_change_display,
    direction,
    timeframe,
    timeframes
  } = prediction;

  // Determine colors based on signal
  const getSignalColor = () => {
    switch (signal) {
      case 'BUY':
      case 'STRONG_BUY':
        return 'bg-green-600 border-green-500';
      case 'SELL':
      case 'STRONG_SELL':
        return 'bg-red-600 border-red-500';
      default:
        return 'bg-yellow-600 border-yellow-500';
    }
  };

  const getSignalTextColor = () => {
    switch (signal) {
      case 'BUY':
      case 'STRONG_BUY':
        return 'text-green-400';
      case 'SELL':
      case 'STRONG_SELL':
        return 'text-red-400';
      default:
        return 'text-yellow-400';
    }
  };

  const getConfidenceColor = () => {
    const conf = parseFloat(confidence);
    if (conf >= 80) return 'text-green-400';
    if (conf >= 60) return 'text-yellow-400';
    return 'text-orange-400';
  };

  // Format display values
  const displayConfidence = confidence_display || `${confidence}%`;
  const displayChange = price_change_display || `${price_change > 0 ? '+' : ''}${price_change}%`;
  const changeIsPositive = parseFloat(price_change) > 0;

  return (
    <div className={`p-4 rounded-lg border-2 ${getSignalColor()} bg-opacity-20 backdrop-blur-sm`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl font-bold text-white">{coin}</span>
          {timeframe && (
            <span className="px-2 py-1 text-xs bg-gray-700 rounded text-gray-300">
              {timeframe}
            </span>
          )}
        </div>
        <div className={`px-3 py-1 rounded-full font-bold text-lg ${getSignalColor()} bg-opacity-30`}>
          {signal}
        </div>
      </div>

      {/* Confidence Bar */}
      <div className="mb-4">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm text-gray-400">Confidence</span>
          <span className={`text-lg font-bold ${getConfidenceColor()}`}>
            {displayConfidence}
          </span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-3">
          <div 
            className={`h-3 rounded-full transition-all duration-500 ${
              parseFloat(confidence) >= 80 ? 'bg-green-500' :
              parseFloat(confidence) >= 60 ? 'bg-yellow-500' : 'bg-orange-500'
            }`}
            style={{ width: `${Math.min(parseFloat(confidence), 100)}%` }}
          />
        </div>
      </div>

      {/* Price Info */}
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div className="bg-gray-800 rounded p-2">
          <span className="text-xs text-gray-400 block">Current Price</span>
          <span className="text-lg font-semibold text-white">
            ${price ? price.toLocaleString() : '---'}
          </span>
        </div>
        <div className="bg-gray-800 rounded p-2">
          <span className="text-xs text-gray-400 block">Predicted Price</span>
          <span className={`text-lg font-semibold ${changeIsPositive ? 'text-green-400' : 'text-red-400'}`}>
            ${predicted_price ? predicted_price.toLocaleString() : '---'}
          </span>
        </div>
      </div>

      {/* Price Change */}
      <div className="flex justify-between items-center">
        <span className="text-sm text-gray-400">Expected Change</span>
        <span className={`text-xl font-bold ${changeIsPositive ? 'text-green-400' : 'text-red-400'}`}>
          {displayChange}
        </span>
      </div>

      {/* Direction Indicator */}
      <div className="mt-3 flex items-center gap-2">
        <span className="text-sm text-gray-400">Direction:</span>
        <span className={`font-semibold ${getSignalTextColor()}`}>
          {direction || (changeIsPositive ? 'UP' : 'DOWN')}
        </span>
        <span className="text-2xl">
          {changeIsPositive ? '📈' : '📉'}
        </span>
      </div>

      {/* Timeframes (if available) */}
      {timeframes && timeframes.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <span className="text-xs text-gray-400 block mb-2">Available Timeframes</span>
          <div className="flex gap-2 flex-wrap">
            {timeframes.map((tf, idx) => (
              <span 
                key={idx}
                className="px-2 py-1 text-xs bg-gray-700 rounded text-gray-300"
              >
                {tf}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Timestamp */}
      {prediction.timestamp && (
        <div className="mt-3 text-xs text-gray-500">
          Updated: {new Date(prediction.timestamp).toLocaleString()}
        </div>
      )}
    </div>
  );
};

/**
 * PredictionList Component
 * Displays a list of predictions
 */
export const PredictionList = ({ predictions, title = "Predictions" }) => {
  if (!predictions || predictions.length === 0) {
    return (
      <div className="p-4 bg-gray-800 rounded-lg text-gray-400 text-center">
        No predictions available
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white">{title}</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {predictions.map((pred, idx) => (
          <PredictionCard key={idx} prediction={pred} />
        ))}
      </div>
    </div>
  );
};

/**
 * TopSignalsList Component
 * Displays top signals with emphasis
 */
export const TopSignalsList = ({ signals }) => {
  if (!signals || signals.length === 0) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h3 className="text-xl font-bold text-white flex items-center gap-2">
        <span className="text-2xl">🔥</span> Top Signals
      </h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {signals.map((signal, idx) => (
          <div 
            key={idx}
            className={`p-4 rounded-lg cursor-pointer transition-all hover:scale-105 ${
              signal.signal === 'BUY' 
                ? 'bg-gradient-to-r from-green-900 to-green-800 border border-green-600' 
                : 'bg-gradient-to-r from-red-900 to-red-800 border border-red-600'
            }`}
          >
            <div className="flex justify-between items-center">
              <div>
                <span className="text-2xl font-bold text-white">{signal.coin}</span>
                <span className="ml-2 text-sm text-gray-400">{signal.timeframe}</span>
              </div>
              <div className="text-right">
                <div className={`text-xl font-bold ${
                  signal.signal === 'BUY' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {signal.signal}
                </div>
                <div className="text-sm text-gray-300">
                  {signal.confidence_display || `${signal.confidence}%`}
                </div>
              </div>
            </div>
            <div className="mt-2 flex justify-between text-sm">
              <span className="text-gray-400">
                Price: ${signal.price?.toLocaleString()}
              </span>
              <span className={signal.price_change > 0 ? 'text-green-400' : 'text-red-400'}>
                {signal.price_change_display || `${signal.price_change > 0 ? '+' : ''}${signal.price_change}%`}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PredictionCard;
