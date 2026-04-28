import React, { useEffect } from 'react';

export default function SensorsTab({ sensorHealth, apiBaseUrl }) {
  if (!sensorHealth) {
    return <div className="sensors-tab">Loading sensor data...</div>;
  }

  const sensors = sensorHealth.sensors || {};

  // Helper function to get status color
  const getStatusColor = (status) => {
    return status === 'online' ? '#4ade80' : '#ef4444';
  };

  // Helper function to get status icon
  const getStatusIcon = (status) => {
    return status === 'online' ? '🟢' : '🔴';
  };

  const sensorConfigs = {
    camera: {
      name: 'Camera (Vision)',
      description: 'Detects people count using anonymous head/body detection',
      keys: ['people_count', 'queue_length'],
      status: sensors.camera?.status || 'offline',
    },
    co2: {
      name: 'CO₂ Sensor',
      description: 'Monitors air quality levels in PPM',
      keys: ['co2_level', 'co2_ppm'],
      status: sensors.co2?.status || 'offline',
    },
    humiture: {
      name: 'Temperature & Humidity Sensor',
      description: 'Tracks thermal comfort conditions (Temperature, Humidity)',
      keys: ['temperature', 'humidity'],
      status: sensors.humiture?.status || 'offline',
    },
    sound: {
      name: 'Sound/Noise Sensor',
      description: 'Measures ambient noise level in decibels',
      keys: ['sound_level', 'noise_db'],
      status: sensors.sound?.status || 'offline',
    },
    pir: {
      name: 'Motion Sensor (PIR) - Draft',
      description: 'Detects motion and presence (implementation pending hardware)',
      keys: ['motion_detected', 'motion_count'],
      status: 'offline',
      isDraft: true,
    },
  };

  return (
    <div className="sensors-tab">
      <div className="sensors-header">
        <h3>Connected Sensors & System Health</h3>
        <p className="sensors-subtitle">
          Monitor the status of all IoT sensors feeding data to the dashboard
        </p>
      </div>

      {/* Status Summary */}
      <div className="sensors-summary">
        <div className="summary-item">
          <span className="summary-label">Total Sensors:</span>
          <span className="summary-value">{Object.keys(sensorConfigs).length}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Active:</span>
          <span className="summary-value">
            {Object.values(sensorConfigs).filter((s) => s.status === 'online').length}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Inactive:</span>
          <span className="summary-value">
            {Object.values(sensorConfigs).filter((s) => s.status === 'offline').length}
          </span>
        </div>
      </div>

      {/* Sensor Cards Grid */}
      <div className="sensors-grid">
        {Object.entries(sensorConfigs).map(([key, config]) => (
          <div
            key={key}
            className={`sensor-card ${config.status === 'online' ? 'online' : 'offline'} ${
              config.isDraft ? 'draft' : ''
            }`}
          >
            {config.isDraft && <div className="draft-badge">DRAFT</div>}

            <div className="sensor-header">
              <h4>{config.name}</h4>
              <div className="sensor-status">
                <span className="status-icon">{getStatusIcon(config.status)}</span>
                <span
                  className="status-text"
                  style={{ color: getStatusColor(config.status) }}
                >
                  {config.status === 'online' ? 'ONLINE' : 'OFFLINE'}
                </span>
              </div>
            </div>

            <p className="sensor-description">{config.description}</p>

            <div className="sensor-keys">
              <span className="keys-label">Data Keys:</span>
              <div className="keys-list">
                {config.keys.map((k) => (
                  <code key={k} className="key-tag">
                    {k}
                  </code>
                ))}
              </div>
            </div>

            {config.status === 'online' && (
              <div className="sensor-actions">
                <button className="btn btn-small btn-secondary">View Data</button>
                <button className="btn btn-small btn-secondary">Calibrate</button>
              </div>
            )}

            {config.status === 'offline' && (
              <div className="offline-notice">
                <p>
                  {config.isDraft
                    ? '⚠️ This sensor is in draft status. Hardware setup pending.'
                    : '⚠️ Sensor is currently offline. Check connection and power.'}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Sensor Network Diagram */}
      <div className="sensor-network">
        <h3>System Architecture</h3>
        <div className="network-diagram">
          <svg viewBox="0 0 800 300" className="architecture-svg">
            {/* ThingsBoard */}
            <rect x="50" y="50" width="150" height="60" fill="#2563eb" rx="5" />
            <text x="127" y="85" textAnchor="middle" fill="white" fontSize="14">
              ThingsBoard
            </text>

            {/* Sensors */}
            <g>
              {/* Camera */}
              <circle cx="150" cy="200" r="30" fill="#3b82f6" />
              <text x="150" y="210" textAnchor="middle" fill="white" fontSize="12">
                📷 Camera
              </text>

              {/* CO2 */}
              <circle cx="250" cy="200" r="30" fill="#3b82f6" />
              <text x="250" y="210" textAnchor="middle" fill="white" fontSize="12">
                💨 CO₂
              </text>

              {/* Temperature */}
              <circle cx="350" cy="200" r="30" fill="#3b82f6" />
              <text x="350" y="210" textAnchor="middle" fill="white" fontSize="12">
                🌡️ Temp/Hum
              </text>

              {/* Sound */}
              <circle cx="450" cy="200" r="30" fill="#3b82f6" />
              <text x="450" y="210" textAnchor="middle" fill="white" fontSize="12">
                🔊 Sound
              </text>

              {/* Motion (Draft) */}
              <circle cx="550" cy="200" r="30" fill="#9ca3af" opacity="0.5" />
              <text x="550" y="210" textAnchor="middle" fill="white" fontSize="12">
                🚨 PIR
              </text>
            </g>

            {/* Connection lines to ThingsBoard */}
            <line
              x1="150"
              y1="170"
              x2="125"
              y2="110"
              stroke="#64748b"
              strokeWidth="2"
              strokeDasharray="5,5"
            />
            <line x1="250" y1="170" x2="125" y2="110" stroke="#64748b" strokeWidth="2" />
            <line x1="350" y1="170" x2="125" y2="110" stroke="#64748b" strokeWidth="2" />
            <line x1="450" y1="170" x2="125" y2="110" stroke="#64748b" strokeWidth="2" />
            <line
              x1="550"
              y1="170"
              x2="125"
              y2="110"
              stroke="#9ca3af"
              strokeWidth="2"
              strokeDasharray="5,5"
              opacity="0.5"
            />

            {/* Backend API */}
            <rect x="300" y="50" width="150" height="60" fill="#059669" rx="5" />
            <text x="375" y="85" textAnchor="middle" fill="white" fontSize="14">
              Backend API
            </text>

            {/* Connection ThingsBoard to API */}
            <line x1="200" y1="80" x2="300" y2="80" stroke="#64748b" strokeWidth="2" />
            <text x="250" y="70" textAnchor="middle" fontSize="12" fill="#64748b">
              REST API
            </text>

            {/* Frontend Dashboard */}
            <rect x="550" y="50" width="150" height="60" fill="#7c2d12" rx="5" />
            <text x="625" y="85" textAnchor="middle" fill="white" fontSize="14">
              Dashboard UI
            </text>

            {/* Connection API to Dashboard */}
            <line x1="450" y1="80" x2="550" y2="80" stroke="#64748b" strokeWidth="2" />
            <text x="500" y="70" textAnchor="middle" fontSize="12" fill="#64748b">
              Real-time
            </text>

            {/* Legend */}
            <text x="50" y="280" fontSize="12" fill="#6b7280">
              🟢 Online
            </text>
            <text x="150" y="280" fontSize="12" fill="#6b7280">
              🔴 Offline
            </text>
            <text x="250" y="280" fontSize="12" fill="#6b7280">
              —— Connected
            </text>
            <text x="400" y="280" fontSize="12" fill="#6b7280">
              - - - Pending
            </text>
          </svg>
        </div>
      </div>

      {/* Troubleshooting Guide */}
      <div className="troubleshooting">
        <h3>Troubleshooting Guide</h3>
        <div className="troubleshooting-items">
          <div className="troubleshooting-item">
            <h4>Camera Sensor Offline</h4>
            <ul>
              <li>Check Pi Camera is connected and enabled in raspi-config</li>
              <li>Verify vision_latest.json file exists and is readable</li>
              <li>Review hardware/vision/camera_logic.py logs</li>
            </ul>
          </div>

          <div className="troubleshooting-item">
            <h4>CO₂ Sensor Offline</h4>
            <ul>
              <li>Verify PCF8591 module is connected via I2C</li>
              <li>Run `i2cdetect -y 1` to check device address</li>
              <li>Review hardware/drivers/co2_sensor.py logs</li>
            </ul>
          </div>

          <div className="troubleshooting-item">
            <h4>Temperature/Humidity Offline</h4>
            <ul>
              <li>Verify DHT11 sensor is connected to correct GPIO pin</li>
              <li>Check power supply is stable (DHT11 is sensitive)</li>
              <li>Review hardware/drivers/Humiture_Sensor.py logs</li>
            </ul>
          </div>

          <div className="troubleshooting-item">
            <h4>Sound Sensor Offline</h4>
            <ul>
              <li>Verify sound sensor module is connected</li>
              <li>Test analog input via PCF8591</li>
              <li>Review hardware/drivers/sound_sensor.py logs</li>
            </ul>
          </div>

          <div className="troubleshooting-item">
            <h4>Connection to ThingsBoard Fails</h4>
            <ul>
              <li>Verify ThingsBoard server is running and accessible</li>
              <li>Check THINGSBOARD_HOST in .env file</li>
              <li>Verify MQTT port 1883 is open</li>
              <li>Confirm ACCESS_TOKEN is correct for each device</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
