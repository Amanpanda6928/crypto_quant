import React, { useState, useEffect } from 'react';
import MetricCard from '../components/MetricCard';
import SignalCard from '../components/SignalCard';

const Dashboard = () => {
  const [signals, setSignals] = useState([]);
  const [metrics, setMetrics] = useState({
    totalValue: '$12,450.67',
    dailyReturn: '+2.34%',
    winRate: '68.5%',
    activePositions: '12'
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate loading data
    const loadData = async () => {
      setTimeout(() => {
        setSignals([
          {
            symbol: 'BTCUSDT',
            signal: 'BUY',
            confidence: 0.87,
            probability: 0.72,
            horizon: '5m',
            timestamp: new Date().toISOString()
          },
          {
            symbol: 'ETHUSDT',
            signal: 'SELL',
            confidence: 0.91,
            probability: 0.68,
            horizon: '10m',
            timestamp: new Date().toISOString()
          },
          {
            symbol: 'SOLUSDT',
            signal: 'BUY',
            confidence: 0.78,
            probability: 0.65,
            horizon: '30m',
            timestamp: new Date().toISOString()
          }
        ]);
        setIsLoading(false);
      }, 1000);
    };

    loadData();
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white">Trading Dashboard</h1>
          <p className="text-gray-400 mt-2">Real-time cryptocurrency trading signals and portfolio overview</p>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Portfolio Value"
            value={metrics.totalValue}
            change="+2.34%"
            changeType="positive"
            icon="💰"
            color="green"
          />
          <MetricCard
            title="Daily Return"
            value={metrics.dailyReturn}
            change="+0.23%"
            changeType="positive"
            icon="📈"
            color="green"
          />
          <MetricCard
            title="Win Rate"
            value={metrics.winRate}
            change="+5.2%"
            changeType="positive"
            icon="🎯"
            color="blue"
          />
          <MetricCard
            title="Active Positions"
            value={metrics.activePositions}
            icon="📊"
            color="yellow"
          />
        </div>

        {/* Signals Section */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Latest Signals</h2>
            <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-md text-sm font-medium transition-colors">
              View All
            </button>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {signals.map((signal, index) => (
                <SignalCard key={index} signal={signal} />
              ))}
            </div>
          )}
        </div>

        {/* System Status */}
        <div className="mt-8 bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h3 className="text-lg font-semibold text-white mb-4">System Status</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-300">Data Pipeline: Online</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-300">ML Models: Active</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              <span className="text-gray-300">Trading Engine: Running</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;