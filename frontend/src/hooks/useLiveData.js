import { useState, useEffect, useCallback } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const POLL_INTERVAL = 900000; // 15 minutes in milliseconds

/**
 * Hook for fetching live automation data every 15 minutes
 * Used for 24/7 market data, predictions, and signals
 */
export function useLiveAutomationData(token, interval = POLL_INTERVAL) {
  const [data, setData] = useState({
    priceData: {},
    predictions: {},
    signals: [],
    loading: true,
    error: null,
    lastUpdate: null
  });

  const fetchLiveData = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/automation/live-data`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      setData({
        priceData: result.price_data || {},
        predictions: result.predictions || {},
        signals: result.signals || [],
        loading: false,
        error: null,
        lastUpdate: new Date()
      });
    } catch (err) {
      setData(prev => ({
        ...prev,
        loading: false,
        error: err.message,
        lastUpdate: new Date()
      }));
    }
  }, [token]);

  useEffect(() => {
    // Initial fetch
    fetchLiveData();

    // Set up polling every 30 seconds
    const intervalId = setInterval(fetchLiveData, interval);

    return () => clearInterval(intervalId);
  }, [fetchLiveData, interval]);

  return { ...data, refetch: fetchLiveData };
}

/**
 * Hook for fetching automation status every 15 minutes
 */
export function useAutomationStatus(token, interval = POLL_INTERVAL) {
  const [status, setStatus] = useState({
    running: false,
    coinsTracked: 0,
    predictionsCount: 0,
    signalsCount: 0,
    lastFetch: null,
    lastPrediction: null,
    loading: true,
    error: null
  });

  const fetchStatus = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/automation/status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      setStatus({
        running: result.running || false,
        coinsTracked: result.coins_tracked || 0,
        predictionsCount: result.predictions_count || 0,
        signalsCount: result.signals_count || 0,
        lastFetch: result.last_fetch ? new Date(result.last_fetch) : null,
        lastPrediction: result.last_prediction ? new Date(result.last_prediction) : null,
        loading: false,
        error: null
      });
    } catch (err) {
      setStatus(prev => ({
        ...prev,
        running: false,
        loading: false,
        error: err.message
      }));
    }
  }, [token]);

  useEffect(() => {
    fetchStatus();
    const intervalId = setInterval(fetchStatus, interval);
    return () => clearInterval(intervalId);
  }, [fetchStatus, interval]);

  return { ...status, refetch: fetchStatus };
}

/**
 * Hook for fetching latest signals every 15 minutes
 */
export function useSignals(token, interval = POLL_INTERVAL) {
  const [signals, setSignals] = useState({
    data: [],
    count: 0,
    loading: true,
    error: null
  });

  const fetchSignals = useCallback(async () => {
    if (!token) return;

    try {
      const response = await fetch(`${API_URL}/api/automation/signals`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      setSignals({
        data: result.signals || [],
        count: result.count || 0,
        loading: false,
        error: null
      });
    } catch (err) {
      setSignals(prev => ({
        ...prev,
        loading: false,
        error: err.message
      }));
    }
  }, [token]);

  useEffect(() => {
    fetchSignals();
    const intervalId = setInterval(fetchSignals, interval);
    return () => clearInterval(intervalId);
  }, [fetchSignals, interval]);

  return { ...signals, refetch: fetchSignals };
}

/**
 * Hook for fetching market data history every 15 minutes
 */
export function useMarketDataHistory(token, coin = null, limit = 100, interval = POLL_INTERVAL) {
  const [data, setData] = useState({
    data: [],
    count: 0,
    loading: true,
    error: null
  });

  const fetchData = useCallback(async () => {
    if (!token) return;

    try {
      const url = new URL(`${API_URL}/api/market-data/latest`);
      if (coin) url.searchParams.append('coin', coin);
      url.searchParams.append('limit', limit.toString());

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      
      setData({
        data: result.data || [],
        count: result.count || 0,
        loading: false,
        error: null
      });
    } catch (err) {
      setData(prev => ({
        ...prev,
        loading: false,
        error: err.message
      }));
    }
  }, [token, coin, limit]);

  useEffect(() => {
    fetchData();
    const intervalId = setInterval(fetchData, interval);
    return () => clearInterval(intervalId);
  }, [fetchData, interval]);

  return { ...data, refetch: fetchData };
}
