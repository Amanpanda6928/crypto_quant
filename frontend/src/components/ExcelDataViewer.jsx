import React, { useState, useEffect } from 'react';
import {
  getDashboardDataExcel,
  getCoinPredictionExcel,
  reloadExcelData,
  downloadLatestExcel
} from '../api/excelApi';

/**
 * ExcelDataViewer Component
 * Demonstrates how to use Excel-based API in React components
 */
const ExcelDataViewer = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedCoin, setSelectedCoin] = useState('BTC');

  // Load dashboard data on mount
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getDashboardDataExcel();
      setData(result);
    } catch (err) {
      setError('Failed to load Excel data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCoinSelect = async (coin) => {
    setSelectedCoin(coin);
    try {
      const result = await getCoinPredictionExcel(coin);
      console.log(`${coin} prediction:`, result);
      alert(`${coin} Signal: ${result.signal} (${result.confidence_display || result.confidence + '%'} confidence)`);
    } catch (err) {
      alert('Error: ' + err.message);
    }
  };

  const handleReload = async () => {
    try {
      await reloadExcelData();
      await loadDashboardData();
      alert('Excel data reloaded successfully!');
    } catch (err) {
      alert('Reload failed: ' + err.message);
    }
  };

  const handleDownload = () => {
    downloadLatestExcel();
  };

  if (loading) return <div className="p-4">Loading Excel data...</div>;
  if (error) return <div className="p-4 text-red-500">{error}</div>;

  return (
    <div className="p-4 bg-gray-900 text-white rounded-lg">
      <h2 className="text-xl font-bold mb-4">📊 Excel Data Viewer</h2>
      
      {/* Controls */}
      <div className="flex gap-2 mb-4">
        <button 
          onClick={handleReload}
          className="px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
        >
          🔄 Reload Data
        </button>
        <button 
          onClick={handleDownload}
          className="px-4 py-2 bg-green-600 rounded hover:bg-green-700"
        >
          📥 Download Excel
        </button>
      </div>

      {/* Status */}
      {data?.status && (
        <div className="mb-4 p-3 bg-gray-800 rounded">
          <p><strong>Status:</strong> {data.status.status}</p>
          <p><strong>File:</strong> {data.status.excel_file}</p>
          <p><strong>Predictions:</strong> {data.status.total_predictions}</p>
          <p><strong>Coins:</strong> {data.status.coins?.length || 0}</p>
        </div>
      )}

      {/* Top Signals */}
      {data?.topSignals?.length > 0 && (
        <div className="mb-4">
          <h3 className="text-lg font-semibold mb-2">🔥 Top Signals</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {data.topSignals.map((signal, idx) => (
              <div 
                key={idx}
                onClick={() => handleCoinSelect(signal.coin)}
                className={`p-3 rounded cursor-pointer hover:opacity-80 ${
                  signal.signal === 'BUY' ? 'bg-green-800' : 'bg-red-800'
                }`}
              >
                <div className="flex justify-between">
                  <span className="font-bold">{signal.coin}</span>
                  <span className={`font-semibold ${
                    signal.signal === 'BUY' ? 'text-green-300' : 'text-red-300'
                  }`}>{signal.signal}</span>
                </div>
                <div className="text-sm text-gray-300">
                  Confidence: <span className="text-white font-medium">{signal.confidence_display || signal.confidence + '%'}</span> | 
                  Change: <span className={`font-medium ${signal.price_change > 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {signal.price_change_display || (signal.price_change > 0 ? '+' : '') + signal.price_change.toFixed(2) + '%'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Coins */}
      {data?.coins?.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-2">🪙 All Coins ({data.coins.length})</h3>
          <div className="flex flex-wrap gap-2">
            {data.coins.map(coin => (
              <button
                key={coin}
                onClick={() => handleCoinSelect(coin)}
                className={`px-3 py-1 rounded text-sm ${
                  selectedCoin === coin 
                    ? 'bg-yellow-600' 
                    : 'bg-gray-700 hover:bg-gray-600'
                }`}
              >
                {coin}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Timestamp */}
      {data?.timestamp && (
        <p className="mt-4 text-sm text-gray-400">
          Last updated: {new Date(data.timestamp).toLocaleString()}
        </p>
      )}
    </div>
  );
};

export default ExcelDataViewer;
