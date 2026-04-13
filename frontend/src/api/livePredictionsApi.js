import api from './api';

/**
 * Fetch all live predictions with backtesting data from backend API
 */
export const getLivePredictions = async () => {
  try {
    const response = await api.get('/api/live-predictions/all');
    return response.data;
  } catch (error) {
    console.error('Error fetching live predictions:', error);
    throw error;
  }
};

/**
 * Get predictions for a specific coin
 */
export const getCoinPredictions = async (coin) => {
  try {
    const response = await api.get(`/api/live-predictions/coin/${coin}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching predictions for ${coin}:`, error);
    throw error;
  }
};

/**
 * Get top signals sorted by confidence
 */
export const getTopSignals = async (minConfidence = 60, limit = 10) => {
  try {
    const response = await api.get(`/api/live-predictions/top-signals?min_confidence=${minConfidence}&limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching top signals:', error);
    throw error;
  }
};

/**
 * Force refresh all predictions
 */
export const refreshPredictions = async () => {
  try {
    const response = await api.post('/api/live-predictions/refresh');
    return response.data;
  } catch (error) {
    console.error('Error refreshing predictions:', error);
    throw error;
  }
};

/**
 * Get backtesting data for a specific coin
 */
export const getCoinBacktest = async (coin, timeframe = '1h') => {
  try {
    const response = await api.get(`/api/live-predictions/backtest/${coin}?timeframe=${timeframe}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching backtest for ${coin}:`, error);
    throw error;
  }
};

export default {
  getLivePredictions,
  getCoinPredictions,
  getTopSignals,
  refreshPredictions,
  getCoinBacktest
};
