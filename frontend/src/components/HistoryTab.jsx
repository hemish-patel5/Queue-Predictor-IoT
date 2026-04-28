import React, { useState, useEffect } from 'react';

export default function HistoryTab({ apiBaseUrl }) {
  const [history, setHistory] = useState(null);
  const [hours, setHours] = useState(6);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await fetch(
          `${apiBaseUrl}/api/v1/history?hours=${hours}&limit=100`
        );
        if (!response.ok) throw new Error('Failed to fetch history');
        const data = await response.json();
        setHistory(data);
      } catch (error) {
        console.error('Error fetching history:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [hours, apiBaseUrl]);

  if (loading) {
    return <div className="history-tab">Loading historical data...</div>;
  }

  return (
    <div className="history-tab">
      <div className="history-controls">
        <label htmlFor="hours-select">Show data for last:</label>
        <select
          id="hours-select"
          value={hours}
          onChange={(e) => setHours(parseInt(e.target.value))}
        >
          <option value={1}>1 hour</option>
          <option value={3}>3 hours</option>
          <option value={6}>6 hours</option>
          <option value={12}>12 hours</option>
          <option value={24}>24 hours</option>
        </select>
      </div>

      <div className="history-content">
        <div className="history-chart">
          <h3>Queue History</h3>
          <div className="chart-placeholder">
            <p>📊 Queue Occupancy Timeline</p>
            <p className="chart-hint">
              Integration with charting library (Chart.js or Recharts recommended)
            </p>
            <svg viewBox="0 0 400 200" className="simple-chart">
              <line
                x1="20"
                y1="180"
                x2="380"
                y2="180"
                stroke="#ccc"
                strokeWidth="2"
              />
              <line
                x1="20"
                y1="20"
                x2="20"
                y2="180"
                stroke="#ccc"
                strokeWidth="2"
              />
              {/* Simple bars representing data */}
              <rect x="40" y="140" width="20" height="40" fill="#3b82f6" />
              <rect x="80" y="100" width="20" height="80" fill="#3b82f6" />
              <rect x="120" y="80" width="20" height="100" fill="#3b82f6" />
              <rect x="160" y="120" width="20" height="60" fill="#3b82f6" />
              <rect x="200" y="60" width="20" height="120" fill="#3b82f6" />
              <rect x="240" y="100" width="20" height="80" fill="#3b82f6" />
              <rect x="280" y="110" width="20" height="70" fill="#3b82f6" />
              <rect x="320" y="130" width="20" height="50" fill="#3b82f6" />
            </svg>
          </div>
        </div>

        <div className="history-chart">
          <h3>Environmental Conditions</h3>
          <div className="chart-placeholder">
            <p>🌡️ Temperature, CO₂, and Noise Trends</p>
            <p className="chart-hint">
              Shows correlation between occupancy and environmental factors
            </p>
            <svg viewBox="0 0 400 200" className="simple-chart">
              <line
                x1="20"
                y1="180"
                x2="380"
                y2="180"
                stroke="#ccc"
                strokeWidth="2"
              />
              <line
                x1="20"
                y1="20"
                x2="20"
                y2="180"
                stroke="#ccc"
                strokeWidth="2"
              />
              {/* Multiple lines for different metrics */}
              <polyline
                points="40,120 80,100 120,90 160,110 200,70 240,100 280,110 320,130"
                stroke="#ef4444"
                strokeWidth="2"
                fill="none"
              />
              <polyline
                points="40,130 80,120 120,110 160,130 200,90 240,120 280,125 320,140"
                stroke="#3b82f6"
                strokeWidth="2"
                fill="none"
              />
              <polyline
                points="40,110 80,100 120,95 160,115 200,75 240,105 280,115 320,125"
                stroke="#10b981"
                strokeWidth="2"
                fill="none"
              />
            </svg>
            <div className="chart-legend">
              <span style={{ color: '#ef4444' }}>— Temperature</span>
              <span style={{ color: '#3b82f6' }}>— CO₂ Level</span>
              <span style={{ color: '#10b981' }}>— Noise Level</span>
            </div>
          </div>
        </div>

        <div className="history-tips">
          <h4>💡 Insights</h4>
          <ul>
            <li>
              <strong>Peak Times:</strong> Notice when the queue is busiest to plan your
              visits accordingly
            </li>
            <li>
              <strong>Environmental Impact:</strong> See how occupancy affects comfort
              metrics
            </li>
            <li>
              <strong>Best Visit Times:</strong> Identify quietest periods for a better
              experience
            </li>
            <li>
              <strong>Air Quality Correlation:</strong> Higher occupancy often means
              higher CO₂ levels
            </li>
          </ul>
        </div>
      </div>

      <div className="implementation-note">
        <p>
          <strong>📝 Implementation Note:</strong> For full functionality, integrate with
          a charting library like <code>Chart.js</code>, <code>Recharts</code>, or{' '}
          <code>Victory</code>. The backend returns telemetry data from ThingsBoard that
          can be visualized here.
        </p>
      </div>
    </div>
  );
}
