import React from 'react';

const MetricCard = ({ title, value, change, changeType, icon, color = 'blue' }) => {
  const getChangeColor = (changeType) => {
    switch (changeType) {
      case 'positive':
        return 'text-green-400';
      case 'negative':
        return 'text-red-400';
      default:
        return 'text-gray-400';
    }
  };

  const getBgColor = (color) => {
    switch (color) {
      case 'green':
        return 'bg-green-500';
      case 'red':
        return 'bg-red-500';
      case 'yellow':
        return 'bg-yellow-500';
      case 'blue':
      default:
        return 'bg-blue-500';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm font-medium">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>

          {change && (
            <div className="flex items-center mt-2">
              <span className={`text-sm font-medium ${getChangeColor(changeType)}`}>
                {change}
              </span>
            </div>
          )}
        </div>

        <div className={`p-3 rounded-full ${getBgColor(color)} bg-opacity-20`}>
          <span className="text-2xl">{icon}</span>
        </div>
      </div>
    </div>
  );
};

export default MetricCard;