import React, { useState } from 'react';

export default function SettingsTab({ apiBaseUrl }) {
  const [settings, setSettings] = useState({
    location: 'IT Helpdesk',
    refreshInterval: 5,
    theme: 'dark',
    notifications: true,
    llmAdvisory: true,
    apiUrl: apiBaseUrl,
  });

  const [saved, setSaved] = useState(false);

  const handleChange = (field, value) => {
    setSettings((prev) => ({
      ...prev,
      [field]: value,
    }));
    setSaved(false);
  };

  const handleSave = () => {
    localStorage.setItem('dashboard-settings', JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="settings-tab">
      <div className="settings-header">
        <h3>Dashboard Settings</h3>
        <p className="settings-subtitle">Configure dashboard behavior and appearance</p>
      </div>

      <div className="settings-content">
        {saved && <div className="success-message">✓ Settings saved successfully!</div>}

        {/* Display Settings */}
        <div className="settings-section">
          <h4>Display Settings</h4>

          <div className="setting-item">
            <label htmlFor="location-input">
              Service Location Name:
              <span className="setting-description">
                Used in advisory messages (e.g., "IT Helpdesk")
              </span>
            </label>
            <input
              id="location-input"
              type="text"
              value={settings.location}
              onChange={(e) => handleChange('location', e.target.value)}
              placeholder="Enter location name"
            />
          </div>

          <div className="setting-item">
            <label htmlFor="theme-select">
              Theme:
              <span className="setting-description">Choose your preferred color scheme</span>
            </label>
            <select
              id="theme-select"
              value={settings.theme}
              onChange={(e) => handleChange('theme', e.target.value)}
            >
              <option value="dark">Dark Mode (Default)</option>
              <option value="light">Light Mode</option>
              <option value="auto">Auto (System)</option>
            </select>
          </div>
        </div>

        {/* Data Settings */}
        <div className="settings-section">
          <h4>Data Settings</h4>

          <div className="setting-item">
            <label htmlFor="refresh-input">
              Data Refresh Interval:
              <span className="setting-description">
                How often to fetch new data from sensors (seconds)
              </span>
            </label>
            <div className="input-group">
              <input
                id="refresh-input"
                type="number"
                min="2"
                max="60"
                value={settings.refreshInterval}
                onChange={(e) =>
                  handleChange('refreshInterval', parseInt(e.target.value))
                }
              />
              <span className="unit">seconds</span>
            </div>
          </div>

          <div className="setting-item">
            <label htmlFor="api-input">
              API Base URL:
              <span className="setting-description">Backend API server address</span>
            </label>
            <input
              id="api-input"
              type="url"
              value={settings.apiUrl}
              onChange={(e) => handleChange('apiUrl', e.target.value)}
              placeholder="http://localhost:8000"
            />
          </div>
        </div>

        {/* Feature Toggles */}
        <div className="settings-section">
          <h4>Features</h4>

          <div className="setting-item checkbox">
            <input
              id="notifications-toggle"
              type="checkbox"
              checked={settings.notifications}
              onChange={(e) => handleChange('notifications', e.target.checked)}
            />
            <label htmlFor="notifications-toggle">
              Enable Notifications
              <span className="setting-description">
                Browser notifications for queue alerts
              </span>
            </label>
          </div>

          <div className="setting-item checkbox">
            <input
              id="llm-toggle"
              type="checkbox"
              checked={settings.llmAdvisory}
              onChange={(e) => handleChange('llmAdvisory', e.target.checked)}
            />
            <label htmlFor="llm-toggle">
              Use LLM-Generated Advisory Messages
              <span className="setting-description">
                AI-powered natural language recommendations (requires backend setup)
              </span>
            </label>
          </div>
        </div>

        {/* Save Button */}
        <div className="settings-actions">
          <button className="btn btn-primary" onClick={handleSave}>
            💾 Save Settings
          </button>
          <button
            className="btn btn-secondary"
            onClick={() => {
              localStorage.removeItem('dashboard-settings');
              location.reload();
            }}
          >
            Reset to Defaults
          </button>
        </div>
      </div>

      {/* System Information */}
      <div className="system-info">
        <h3>System Information</h3>

        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Dashboard Version:</span>
            <span className="info-value">1.0.0</span>
          </div>
          <div className="info-item">
            <span className="info-label">Backend API:</span>
            <span className="info-value">{settings.apiUrl}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Environment:</span>
            <span className="info-value">
              {import.meta.env.MODE === 'development' ? 'Development' : 'Production'}
            </span>
          </div>
        </div>

        <div className="browser-info">
          <h4>Browser Information</h4>
          <ul>
            <li>User Agent: {navigator.userAgent}</li>
            <li>Platform: {navigator.platform}</li>
            <li>Language: {navigator.language}</li>
          </ul>
        </div>
      </div>

      {/* Integration Guide */}
      <div className="integration-guide">
        <h3>Integration Guide</h3>

        <div className="guide-section">
          <h4>🔌 Setting Up Sensor Integration</h4>
          <ol>
            <li>
              <strong>Ensure all sensors are connected</strong> and wired to the Raspberry
              Pi
            </li>
            <li>
              <strong>Run sensor driver scripts:</strong>
              <code>python3 hardware/drivers/co2_sensor.py</code>
            </li>
            <li>
              <strong>Verify ThingsBoard connection:</strong> Check that telemetry data is
              appearing in ThingsBoard UI
            </li>
            <li>
              <strong>Start the backend API:</strong>
              <code>cd backend && python3 -m uvicorn services.API_server:app</code>
            </li>
            <li>
              <strong>Configure API URL</strong> in settings above if backend is not on
              localhost
            </li>
            <li>
              <strong>Refresh dashboard</strong> to start seeing live data
            </li>
          </ol>
        </div>

        <div className="guide-section">
          <h4>📊 Understanding the Dashboard</h4>
          <ul>
            <li>
              <strong>Live Status:</strong> Shows real-time queue count and wait estimates
            </li>
            <li>
              <strong>Advisory Message:</strong> AI-generated recommendation based on all
              metrics
            </li>
            <li>
              <strong>Environmental Metrics:</strong> Current sensor readings with comfort
              scores
            </li>
            <li>
              <strong>History:</strong> Trends over time to identify peak periods
            </li>
            <li>
              <strong>Sensors:</strong> Health status of all connected devices
            </li>
          </ul>
        </div>

        <div className="guide-section">
          <h4>🔒 Privacy & Security</h4>
          <ul>
            <li>
              <strong>No facial recognition:</strong> Only anonymous head/body detection is
              used
            </li>
            <li>
              <strong>Local processing:</strong> Video data is processed locally on the Pi
            </li>
            <li>
              <strong>Aggregated data only:</strong> Only queue count is transmitted, not
              individual identities
            </li>
            <li>
              <strong>HTTPS ready:</strong> Deploy with SSL certificates in production
            </li>
          </ul>
        </div>
      </div>

      {/* About */}
      <div className="about-section">
        <h3>About</h3>
        <p>
          <strong>Queue Time & Comfort Predictor</strong> is an IoT-based system designed
          to help students and staff make informed decisions about when to visit campus
          services.
        </p>
        <p>
          By combining real-time sensor data with AI-powered advisory messages, we provide
          actionable insights about queue times, wait periods, and environmental comfort.
        </p>
        <div className="about-team">
          <h4>Development Team</h4>
          <ul>
            <li>Member 1: Hardware & Computer Vision</li>
            <li>Member 2: Dashboard & UI/UX</li>
            <li>Member 3: Backend & LLM Integration</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
