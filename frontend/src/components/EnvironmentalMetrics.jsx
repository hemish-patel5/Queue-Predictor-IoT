import React from 'react';

export default function EnvironmentalMetrics({ data }) {
  if (!data || !data.environmental_metrics) {
    return <div className="environmental-metrics">Loading...</div>;
  }

  const metrics = data.environmental_metrics;
  const comfortData = data.comfort_data || {};

  // Helper function to get color based on air quality
  const getAirQualityColor = (status) => {
    switch (status) {
      case 'Good':
        return '#4ade80'; // Green
      case 'Fair':
        return '#facc15'; // Yellow
      case 'Poor':
        return '#fb923c'; // Orange
      case 'Critical':
        return '#ef4444'; // Red
      default:
        return '#6b7280'; // Gray
    }
  };

  // Helper function to get color based on noise
  const getNoiseColor = (db) => {
    if (db <= 50) return '#4ade80';
    if (db <= 65) return '#facc15';
    if (db <= 80) return '#fb923c';
    return '#ef4444';
  };

  // Helper function to get thermal comfort color
  const getThermalColor = (status) => {
    if (status === 'Optimal' || status === 'Comfortable') return '#4ade80';
    if (status === 'Too Warm' || status === 'Too Cold') return '#fb923c';
    return '#facc15';
  };

  return (
    <section className="environmental-metrics-section">
      <h3 className="section-title">Environmental Comfort Metrics</h3>

      <div className="metrics-grid">
        {/* Temperature & Humidity */}
        <div className="metric-card">
          <div className="metric-header">
            <h4>Thermal Comfort</h4>
            <span className="metric-icon">🌡️</span>
          </div>
          <div className="thermal-grid">
            <div className="thermal-item">
              <span className="small-label">Temperature</span>
              <span className="value">{metrics.temperature}°C</span>
            </div>
            <div className="thermal-item">
              <span className="small-label">Humidity</span>
              <span className="value">{metrics.humidity}%</span>
            </div>
          </div>
          <div
            className="status-badge"
            style={{ backgroundColor: getThermalColor(metrics.comfort_status) }}
          >
            {metrics.comfort_status}
          </div>
        </div>

        {/* CO2 Level - Traffic Light Style */}
        <div className="metric-card">
          <div className="metric-header">
            <h4>Air Quality (CO₂)</h4>
            <span className="metric-icon">💨</span>
          </div>
          <div className="co2-display">
            <div className="co2-value">{metrics.co2_ppm}</div>
            <div className="co2-unit">ppm</div>
          </div>
          <div
            className="status-badge traffic-light"
            style={{ backgroundColor: getAirQualityColor(metrics.air_quality_status) }}
          >
            {metrics.air_quality_status}
          </div>
          <div className="co2-guide">
            <span className="guide-item">
              <span style={{ color: '#4ade80' }}>●</span> ≤1000 (Good)
            </span>
            <span className="guide-item">
              <span style={{ color: '#facc15' }}>●</span> 1000-1500 (Fair)
            </span>
            <span className="guide-item">
              <span style={{ color: '#ef4444' }}>●</span> &gt;1500 (Poor)
            </span>
          </div>
        </div>

        {/* Noise Level */}
        <div className="metric-card">
          <div className="metric-header">
            <h4>Noise Level</h4>
            <span className="metric-icon">🔊</span>
          </div>
          <div className="noise-display">
            <div className="noise-value">{metrics.noise_db}</div>
            <div className="noise-unit">dB</div>
          </div>
          <div className="noise-bar">
            <div
              className="noise-bar-fill"
              style={{
                width: Math.min((metrics.noise_db / 100) * 100, 100) + '%',
                backgroundColor: getNoiseColor(metrics.noise_db),
              }}
            ></div>
          </div>
          <div className="noise-status">{comfortData.noise_comfort || 'Measuring...'}</div>
        </div>

        {/* Comfort Score */}
        <div className="metric-card comfort-score-card">
          <div className="metric-header">
            <h4>Overall Comfort</h4>
            <span className="metric-icon">✨</span>
          </div>
          <div className="comfort-circle">
            <svg viewBox="0 0 100 100" className="comfort-gauge">
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="8"
              />
              <circle
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke={getAirQualityColor(
                  comfortData.comfort_level === 'Excellent'
                    ? 'Good'
                    : comfortData.comfort_level === 'Good'
                    ? 'Fair'
                    : comfortData.comfort_level === 'Acceptable'
                    ? 'Poor'
                    : 'Critical'
                )}
                strokeWidth="8"
                strokeDasharray={`${(comfortData.comfort_score / 100) * 283} 283`}
                strokeDashoffset="0"
                strokeLinecap="round"
              />
            </svg>
            <div className="comfort-text">
              <div className="comfort-score">{comfortData.comfort_score || 0}</div>
              <div className="comfort-level">{comfortData.comfort_level || 'N/A'}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Breakdown Details */}
      {comfortData.breakdown && (
        <div className="comfort-breakdown">
          <h4>Comfort Breakdown</h4>
          <div className="breakdown-items">
            <div className="breakdown-item">
              <span className="breakdown-label">Thermal:</span>
              <div className="breakdown-bar">
                <div
                  className="breakdown-fill"
                  style={{ width: `${comfortData.thermal_score || 0}%` }}
                ></div>
              </div>
              <span className="breakdown-value">{comfortData.thermal_score || 0}%</span>
            </div>
            <div className="breakdown-item">
              <span className="breakdown-label">Air Quality:</span>
              <div className="breakdown-bar">
                <div
                  className="breakdown-fill"
                  style={{ width: `${comfortData.air_quality_score || 0}%` }}
                ></div>
              </div>
              <span className="breakdown-value">{comfortData.air_quality_score || 0}%</span>
            </div>
            <div className="breakdown-item">
              <span className="breakdown-label">Noise:</span>
              <div className="breakdown-bar">
                <div
                  className="breakdown-fill"
                  style={{ width: `${comfortData.noise_score || 0}%` }}
                ></div>
              </div>
              <span className="breakdown-value">{comfortData.noise_score || 0}%</span>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
