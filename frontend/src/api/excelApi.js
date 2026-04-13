import api from "./api";

/**
 * Excel Data API Service
 * Connects frontend to Excel-based backend APIs
 * Replaces database-dependent operations
 */

const EXCEL_BASE = "/api/predictions-excel";
const LIVE_EXCEL_BASE = "/api/live-excel";
const LIVE_PREDICTIONS_BASE = "/api/live-predictions";
const FINNHUB_BASE = "/api/finnhub";

/**
 * Get all predictions from Excel
 */
export const getAllPredictionsExcel = async () => {
  try {
    // Try live predictions first, fall back to excel
    try {
      const response = await api.get(`${LIVE_PREDICTIONS_BASE}/all`);
      return {
        predictions: response.data.predictions || {},
        count: response.data.count || 0,
        supported_coins: response.data.coins || [],
        timestamp: response.data.last_updated
      };
    } catch (liveError) {
      // Fall back to old endpoint
      const response = await api.get(`${EXCEL_BASE}/live`);
      return response.data;
    }
  } catch (error) {
    console.error("Error fetching Excel predictions:", error);
    throw error;
  }
};

/**
 * Get prediction for a specific coin from Excel
 * @param {string} coin - Cryptocurrency symbol (BTC, ETH, etc.)
 */
export const getCoinPredictionExcel = async (coin) => {
  try {
    const response = await api.get(`${EXCEL_BASE}/live/${coin}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching Excel prediction for ${coin}:`, error);
    throw error;
  }
};

/**
 * Get top signals from Excel
 * @param {number} minConfidence - Minimum confidence (default: 60)
 * @param {number} topN - Number of signals to return
 * @param {string} signalType - Filter by 'BUY' or 'SELL'
 */
export const getTopSignalsExcel = async (minConfidence = 60, topN = 10, signalType = null) => {
  try {
    // Try live predictions first
    try {
      const params = { min_confidence: minConfidence, limit: topN };
      const response = await api.get(`${LIVE_PREDICTIONS_BASE}/top-signals`, { params });
      return {
        signals: response.data.signals || [],
        count: response.data.count || 0
      };
    } catch (liveError) {
      // Fall back to old endpoint
      const params = { min_confidence: minConfidence, top_n: topN };
      if (signalType) params.signal_type = signalType;
      const response = await api.get(`${EXCEL_BASE}/top-signals`, { params });
      return response.data;
    }
  } catch (error) {
    console.error("Error fetching top Excel signals:", error);
    throw error;
  }
};

/**
 * Get detailed prediction with all timeframes for a coin
 * @param {string} coin - Cryptocurrency symbol
 */
export const getDetailedPredictionExcel = async (coin) => {
  try {
    const response = await api.get(`${EXCEL_BASE}/detailed/${coin}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching detailed Excel prediction for ${coin}:`, error);
    throw error;
  }
};

/**
 * Get predictions for a specific timeframe
 * @param {string} timeframe - Time period (30m, 1h, 4h, 1d)
 */
export const getPredictionsByTimeframe = async (timeframe) => {
  try {
    const response = await api.get(`${EXCEL_BASE}/by-timeframe/${timeframe}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching Excel predictions for ${timeframe}:`, error);
    throw error;
  }
};

/**
 * Get summary for all coins
 */
export const getAllCoinsSummary = async () => {
  try {
    const response = await api.get(`${EXCEL_BASE}/summary`);
    return response.data;
  } catch (error) {
    console.error("Error fetching Excel coins summary:", error);
    throw error;
  }
};

/**
 * Reload Excel data
 */
export const reloadExcelData = async () => {
  try {
    const response = await api.post(`${EXCEL_BASE}/reload`);
    return response.data;
  } catch (error) {
    console.error("Error reloading Excel data:", error);
    throw error;
  }
};

/**
 * Generate new AI predictions for all 10 coins
 * Updates the Excel file with fresh predictions
 */
export const generatePredictions = async () => {
  try {
    const response = await api.post(`${LIVE_PREDICTIONS_BASE}/refresh`);
    return response.data;
  } catch (error) {
    console.error("Error generating predictions:", error);
    throw error;
  }
};

/**
 * Get Excel data store status
 */
export const getExcelStatus = async () => {
  try {
    const response = await api.get(`${EXCEL_BASE}/status`);
    return response.data;
  } catch (error) {
    console.error("Error fetching Excel status:", error);
    throw error;
  }
};

/**
 * Live Excel APIs
 */

/**
 * Get live Excel file status
 */
export const getLiveExcelStatus = async () => {
  try {
    const response = await api.get(`${LIVE_EXCEL_BASE}/status`);
    return response.data;
  } catch (error) {
    console.error("Error fetching live Excel status:", error);
    throw error;
  }
};

/**
 * Get raw prediction data from live Excel
 * @param {string} coin - Optional coin filter
 * @param {string} timeframe - Optional timeframe filter
 * @param {number} minConfidence - Minimum confidence
 */
export const getLivePredictionsData = async (coin = null, timeframe = null, minConfidence = 60) => {
  try {
    const params = { min_confidence: minConfidence };
    if (coin) params.coin = coin;
    if (timeframe) params.timeframe = timeframe;
    
    const response = await api.get(`${LIVE_EXCEL_BASE}/data`, { params });
    return response.data;
  } catch (error) {
    console.error("Error fetching live Excel data:", error);
    throw error;
  }
};

/**
 * Force refresh of live predictions
 */
export const refreshLivePredictions = async () => {
  try {
    const response = await api.post(`${LIVE_EXCEL_BASE}/refresh`);
    return response.data;
  } catch (error) {
    console.error("Error refreshing live Excel predictions:", error);
    throw error;
  }
};

/**
 * Download latest Excel file
 */
export const downloadLatestExcel = () => {
  window.open(`http://127.0.0.1:8000${LIVE_EXCEL_BASE}/download`, "_blank");
};

/**
 * Combined API for Dashboard
 * Fetches all data needed for dashboard in one call
 */
export const getDashboardDataExcel = async () => {
  try {
    const [predictions, topSignals, status] = await Promise.all([
      getAllPredictionsExcel(),
      getTopSignalsExcel(60, 10),
      getExcelStatus()
    ]);
    
    return {
      predictions: predictions.predictions || {},
      topSignals: topSignals.signals || [],
      coins: predictions.supported_coins || [],
      count: predictions.count || 0,
      status: status,
      timestamp: predictions.timestamp
    };
  } catch (error) {
    console.error("Error fetching dashboard data:", error);
    throw error;
  }
};

export const handleReload = async () => {
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

/**
 * Finnhub API - Real-time crypto predictions with technical analysis
 */

/**
 * Get all predictions from Finnhub API
 */
export const getAllPredictionsFinnhub = async () => {
  try {
    const response = await api.get(`${FINNHUB_BASE}/all`);
    return {
      predictions: response.data.predictions || {},
      count: response.data.count || 0,
      supported_coins: response.data.coins_tracked || [],
      timestamp: response.data.last_updated,
      source: response.data.source || 'Finnhub',
      method: response.data.method || 'Technical Analysis'
    };
  } catch (error) {
    console.error("Error fetching Finnhub predictions:", error);
    throw error;
  }
};

/**
 * Get predictions for a specific coin from Finnhub
 * @param {string} coin - Cryptocurrency symbol
 */
export const getCoinPredictionFinnhub = async (coin) => {
  try {
    const response = await api.get(`${FINNHUB_BASE}/coin/${coin}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching Finnhub prediction for ${coin}:`, error);
    throw error;
  }
};

/**
 * Get top signals from Finnhub
 * @param {number} minConfidence - Minimum confidence (default: 60)
 * @param {number} limit - Number of signals to return
 * @param {string} signalType - Filter by 'BUY', 'SELL', or 'HOLD'
 */
export const getTopSignalsFinnhub = async (minConfidence = 60, limit = 20, signalType = null) => {
  try {
    const params = { min_confidence: minConfidence, limit };
    if (signalType) params.signal_type = signalType;
    const response = await api.get(`${FINNHUB_BASE}/top-signals`, { params });
    return {
      signals: response.data.signals || [],
      count: response.data.count || 0,
      filters: response.data.filters || {}
    };
  } catch (error) {
    console.error("Error fetching Finnhub top signals:", error);
    throw error;
  }
};

/**
 * Get backtest results for a coin
 * @param {string} coin - Cryptocurrency symbol
 * @param {string} timeframe - Optional timeframe filter
 */
export const getBacktestResults = async (coin, timeframe = null) => {
  try {
    const params = {};
    if (timeframe) params.timeframe = timeframe;
    const response = await api.get(`${FINNHUB_BASE}/backtest/${coin}`, { params });
    return {
      coin: response.data.coin,
      name: response.data.name,
      backtests: response.data.backtests || [],
      count: response.data.count || 0
    };
  } catch (error) {
    console.error(`Error fetching backtest results for ${coin}:`, error);
    throw error;
  }
};

/**
 * Get all backtest results
 */
export const getAllBacktestResults = async () => {
  try {
    const response = await api.get(`${FINNHUB_BASE}/backtest-all`);
    return {
      backtests: response.data.backtests || [],
      count: response.data.count || 0,
      coins: response.data.coins || [],
      timeframes: response.data.timeframes || []
    };
  } catch (error) {
    console.error("Error fetching all backtest results:", error);
    throw error;
  }
};

/**
 * Refresh Finnhub predictions
 */
export const refreshFinnhubPredictions = async () => {
  try {
    const response = await api.post(`${FINNHUB_BASE}/refresh`);
    return response.data;
  } catch (error) {
    console.error("Error refreshing Finnhub predictions:", error);
    throw error;
  }
};

/**
 * Get Finnhub service status
 */
export const getFinnhubStatus = async () => {
  try {
    const response = await api.get(`${FINNHUB_BASE}/status`);
    return response.data;
  } catch (error) {
    console.error("Error fetching Finnhub status:", error);
    throw error;
  }
};

export default {
  getDashboardDataExcel,
  getAllPredictionsExcel,
  getAllPredictionsFinnhub,
  getTopSignalsExcel,
  getTopSignalsFinnhub,
  getCoinPredictionFinnhub,
  getBacktestResults,
  getAllBacktestResults,
  reloadExcelData,
  generatePredictions,
  refreshFinnhubPredictions,
  getPredictionsByTimeframe,
  getAllCoinsSummary,
  getExcelStatus,
  getLiveExcelStatus,
  getFinnhubStatus,
  getLivePredictionsData,
  refreshLivePredictions,
  downloadLatestExcel
};
