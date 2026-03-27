import React from 'react';

const SignalCard = ({ signal }) => {
  const getSignalColor = (signal) => {
    switch (signal.toLowerCase()) {
      case 'buy':
        return 'bg-green-500';
      case 'sell':
        return 'bg-red-500';
      case 'hold':
        return 'bg-yellow-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-gray-600 transition-colors">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${getSignalColor(signal.signal)}`}></div>
          <h3 className="text-lg font-semibold text-white">{signal.symbol}</h3>
        </div>
        <span className={`px-2 py-1 rounded text-xs font-medium ${
          signal.signal === 'BUY' ? 'bg-green-900 text-green-300' :
          signal.signal === 'SELL' ? 'bg-red-900 text-red-300' :
          'bg-yellow-900 text-yellow-300'
        }`}>
          {signal.signal}
        </span>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-gray-400 text-sm">Confidence</span>
          <span className={`font-medium ${getConfidenceColor(signal.confidence)}`}>
            {(signal.confidence * 100).toFixed(1)}%
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-400 text-sm">Probability</span>
          <span className="text-white font-medium">
            {(signal.probability * 100).toFixed(1)}%
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-400 text-sm">Horizon</span>
          <span className="text-white font-medium">{signal.horizon}</span>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-gray-700">
        <div className="text-xs text-gray-500">
          Updated: {new Date(signal.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default SignalCard;