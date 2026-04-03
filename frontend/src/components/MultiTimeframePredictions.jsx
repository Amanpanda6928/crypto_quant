import { useState } from 'react';
import { useLiveAutomationData } from '../hooks/useLiveData';

const TIMEFRAMES = [
  { key: '15m', label: '15 Min', color: '#10b981', desc: 'Short-term' },
  { key: '30m', label: '30 Min', color: '#3b82f6', desc: 'Medium' },
  { key: '1h', label: '1 Hour', color: '#8b5cf6', desc: 'Standard' },
  { key: '4h', label: '4 Hour', color: '#f59e0b', desc: 'Swing' },
  { key: '1d', label: '1 Day', color: '#ef4444', desc: 'Long-term' }
];

const COIN_COLORS = {
  'BTC': '#f7931a', 'ETH': '#627eea', 'BNB': '#f3ba2f', 'SOL': '#9945ff',
  'XRP': '#00aae4', 'ADA': '#0033ad', 'AVAX': '#e84142', 'DOGE': '#c2a633',
  'DOT': '#e6007a', 'LINK': '#2a5ada', 'MATIC': '#8247e5', 'LTC': '#bfbbbb',
  'BCH': '#0ac18e', 'UNI': '#ff007a', 'ATOM': '#6f75c8', 'XLM': '#7d00ff', 'ICP': '#29abe2'
};

export default function MultiTimeframePredictions({ token }) {
  const { predictions, loading, error, lastUpdate } = useLiveAutomationData(token);
  const [selectedCoin, setSelectedCoin] = useState(null);

  // Get all coins from predictions
  const getCoins = () => {
    const coins = new Set();
    Object.values(predictions || {}).forEach(tfData => {
      Object.keys(tfData).forEach(coin => coins.add(coin));
    });
    return Array.from(coins).sort();
  };

  const coins = getCoins();

  // Get prediction for specific coin and timeframe
  const getPrediction = (coin, timeframe) => {
    return predictions?.[timeframe]?.[coin];
  };

  // Get signal color
  const getSignalColor = (signal) => {
    switch (signal) {
      case 'BUY': return '#10b981';
      case 'SELL': return '#ef4444';
      default: return '#f59e0b';
    }
  };

  // Format confidence percentage
  const formatConfidence = (conf) => {
    return conf ? `${(conf * 100).toFixed(1)}%` : '-';
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <h2 style={styles.title}>🔮 Multi-Timeframe Predictions</h2>
          <span style={styles.loading}>Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.header}>
          <h2 style={styles.title}>🔮 Multi-Timeframe Predictions</h2>
          <span style={styles.error}>Error: {error}</span>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>🔮 Multi-Timeframe Predictions</h2>
        <div style={styles.meta}>
          <span style={styles.badge}>⏰ Updates every 15 min</span>
          <span style={styles.coinCount}>📊 {coins.length || 17} coins</span>
          {lastUpdate && (
            <span style={styles.lastUpdate}>
              Last: {lastUpdate.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Timeframe Legend */}
      <div style={styles.legend}>
        {TIMEFRAMES.map(tf => (
          <div key={tf.key} style={{ ...styles.legendItem, borderColor: tf.color }}>
            <span style={{ ...styles.legendDot, background: tf.color }}></span>
            <span style={styles.legendLabel}>{tf.label}</span>
            <span style={styles.legendDesc}>{tf.desc}</span>
          </div>
        ))}
      </div>

      {/* Predictions Grid */}
      <div style={styles.grid}>
        {coins.length === 0 ? (
          <div style={styles.noData}>No predictions available yet. Waiting for 15-minute cycle...</div>
        ) : (
          coins.map(coin => (
            <div 
              key={coin} 
              style={{ 
                ...styles.coinCard, 
                borderColor: COIN_COLORS[coin] || '#667eea',
                background: selectedCoin === coin ? 'rgba(102, 126, 234, 0.1)' : 'transparent'
              }}
              onClick={() => setSelectedCoin(selectedCoin === coin ? null : coin)}
            >
              <div style={{ ...styles.coinHeader, color: COIN_COLORS[coin] || '#667eea' }}>
                <span style={styles.coinSymbol}>{coin}</span>
                <span style={styles.coinIcon}>📊</span>
              </div>
              
              <div style={styles.predictionsRow}>
                {TIMEFRAMES.map(tf => {
                  const pred = getPrediction(coin, tf.key);
                  return (
                    <div 
                      key={tf.key} 
                      style={{ 
                        ...styles.predictionCell,
                        background: pred ? getSignalColor(pred.predicted_direction) + '20' : 'transparent',
                        borderColor: tf.color
                      }}
                      title={pred ? `${tf.label}: ${pred.predicted_direction} (${formatConfidence(pred.confidence)})` : 'No data'}
                    >
                      <div style={{ ...styles.timeframeLabel, color: tf.color }}>{tf.key}</div>
                      {pred ? (
                        <>
                          <div style={{ ...styles.signal, color: getSignalColor(pred.predicted_direction) }}>
                            {pred.predicted_direction}
                          </div>
                          <div style={styles.confidence}>{formatConfidence(pred.confidence)}</div>
                        </>
                      ) : (
                        <div style={styles.noPred}>-</div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Expanded Details */}
              {selectedCoin === coin && (
                <div style={styles.details}>
                  {TIMEFRAMES.map(tf => {
                    const pred = getPrediction(coin, tf.key);
                    if (!pred) return null;
                    return (
                      <div key={tf.key} style={styles.detailRow}>
                        <span style={{ color: tf.color, fontWeight: 'bold' }}>{tf.label}:</span>
                        <span style={{ color: getSignalColor(pred.predicted_direction) }}>
                          {pred.predicted_direction} @ ${pred.current_price?.toFixed(2)}
                        </span>
                        <span>→ Target: ${pred.target_price?.toFixed(2)}</span>
                        <span style={styles.detailConf}>Conf: {formatConfidence(pred.confidence)}</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div style={styles.footer}>
        <p>🔄 17 coins • Predictions refresh every 15 minutes • Timeframes: 15m, 30m, 1h, 4h, 1d</p>
        <p style={styles.footerNote}>Auto-deletes data older than 1 day</p>
      </div>
    </div>
  );
}

const styles = {
  container: {
    background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
    borderRadius: '16px',
    padding: '24px',
    color: '#e2e8f0',
    fontFamily: 'system-ui, -apple-system, sans-serif',
    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
    border: '1px solid #334155'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
    flexWrap: 'wrap',
    gap: '10px'
  },
  title: {
    margin: 0,
    fontSize: '24px',
    fontWeight: '700',
    background: 'linear-gradient(90deg, #667eea, #764ba2)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent'
  },
  meta: {
    display: 'flex',
    gap: '10px',
    alignItems: 'center'
  },
  badge: {
    background: 'rgba(16, 185, 129, 0.2)',
    color: '#10b981',
    padding: '4px 12px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: '600'
  },
  coinCount: {
    background: 'rgba(139, 92, 246, 0.2)',
    color: '#a78bfa',
    padding: '4px 12px',
    borderRadius: '20px',
    fontSize: '12px',
    fontWeight: '600'
  },
  lastUpdate: {
    color: '#94a3b8',
    fontSize: '12px'
  },
  loading: {
    color: '#fbbf24'
  },
  error: {
    color: '#ef4444'
  },
  legend: {
    display: 'flex',
    gap: '15px',
    marginBottom: '20px',
    flexWrap: 'wrap',
    padding: '12px',
    background: 'rgba(0, 0, 0, 0.2)',
    borderRadius: '8px'
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '4px 10px',
    borderRadius: '6px',
    border: '1px solid',
    borderColor: 'transparent',
    fontSize: '13px'
  },
  legendDot: {
    width: '10px',
    height: '10px',
    borderRadius: '50%'
  },
  legendLabel: {
    fontWeight: '600'
  },
  legendDesc: {
    color: '#94a3b8',
    fontSize: '11px'
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '16px',
    marginBottom: '20px'
  },
  coinCard: {
    background: 'rgba(30, 41, 59, 0.8)',
    borderRadius: '12px',
    padding: '16px',
    border: '2px solid',
    cursor: 'pointer',
    transition: 'all 0.3s ease'
  },
  coinHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '12px',
    fontWeight: '700',
    fontSize: '18px'
  },
  coinSymbol: {
    textTransform: 'uppercase'
  },
  coinIcon: {
    fontSize: '20px'
  },
  predictionsRow: {
    display: 'flex',
    gap: '8px',
    justifyContent: 'space-between'
  },
  predictionCell: {
    flex: 1,
    textAlign: 'center',
    padding: '8px 4px',
    borderRadius: '8px',
    border: '1px solid',
    minWidth: '50px'
  },
  timeframeLabel: {
    fontSize: '10px',
    fontWeight: '700',
    marginBottom: '4px',
    textTransform: 'uppercase'
  },
  signal: {
    fontSize: '11px',
    fontWeight: '700',
    marginBottom: '2px'
  },
  confidence: {
    fontSize: '10px',
    color: '#94a3b8'
  },
  noPred: {
    color: '#64748b',
    fontSize: '14px'
  },
  details: {
    marginTop: '12px',
    paddingTop: '12px',
    borderTop: '1px solid #334155',
    fontSize: '13px'
  },
  detailRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '4px 0',
    gap: '8px'
  },
  detailConf: {
    color: '#94a3b8',
    fontSize: '11px'
  },
  noData: {
    textAlign: 'center',
    padding: '40px',
    color: '#94a3b8',
    fontSize: '16px'
  },
  footer: {
    textAlign: 'center',
    color: '#64748b',
    fontSize: '12px',
    marginTop: '16px',
    paddingTop: '16px',
    borderTop: '1px solid #334155'
  },
  footerNote: {
    marginTop: '4px',
    fontSize: '11px'
  }
};
