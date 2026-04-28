import React, { useState, useEffect, useRef } from 'react';
import './App.css';

// Components
import LiveStatusSection from './components/LiveStatusSection';
import EnvironmentalMetrics from './components/EnvironmentalMetrics';
import HistoryTab from './components/HistoryTab';
import SensorsTab from './components/SensorsTab';
import SettingsTab from './components/SettingsTab';

function App() {
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [liveData, setLiveData] = useState(null);
  const [sensorHealth, setSensorHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const dataFetchIntervalRef = useRef(null);

  // API Configuration
  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  // Fetch live data
  const fetchLiveData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/live-status`);
      if (!response.ok) throw new Error('Failed to fetch live data');
      const data = await response.json();
      setLiveData(data);
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Error fetching live data:', err);
      setError('Failed to connect to backend. Make sure the API server is running.');
    }
  };

  // Fetch sensor health
  const fetchSensorHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/sensor-health`);
      if (!response.ok) throw new Error('Failed to fetch sensor health');
      const data = await response.json();
      setSensorHealth(data);
    } catch (err) {
      console.error('Error fetching sensor health:', err);
    }
  };

  // Initial data fetch and setup polling
  useEffect(() => {
    fetchLiveData();
    fetchSensorHealth();
    setLoading(false);

    // Poll for new data every 5 seconds
    dataFetchIntervalRef.current = setInterval(() => {
      fetchLiveData();
      fetchSensorHealth();
    }, 5000);

    return () => {
      if (dataFetchIntervalRef.current) {
        clearInterval(dataFetchIntervalRef.current);
      }
    };
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    await fetchLiveData();
    await fetchSensorHealth();
    setLoading(false);
  };

  if (loading && !liveData) {
    return (
      <div className="app-container loading">
        <div className="loading-spinner">
          <div className="spinner"></div>
          <p>Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <h1 className="app-title">Queue Time & Comfort<br />Predictor</h1>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${currentTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentTab('dashboard')}
          >
            <span className="nav-icon">📊</span>
            Dashboard
          </button>
          <button
            className={`nav-item ${currentTab === 'history' ? 'active' : ''}`}
            onClick={() => setCurrentTab('history')}
          >
            <span className="nav-icon">📈</span>
            History
          </button>
          <button
            className={`nav-item ${currentTab === 'sensors' ? 'active' : ''}`}
            onClick={() => setCurrentTab('sensors')}
          >
            <span className="nav-icon">🔌</span>
            Sensors
          </button>
          <button
            className={`nav-item ${currentTab === 'settings' ? 'active' : ''}`}
            onClick={() => setCurrentTab('settings')}
          >
            <span className="nav-icon">⚙️</span>
            Settings
          </button>
        </nav>

        <div className="sidebar-footer">
          <p className="privacy-notice">
            🔒 Active: Anonymous Head/Body Detection Only
          </p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {/* Header */}
        <header className="dashboard-header">
          <h2>
            {currentTab === 'dashboard' && 'Live Dashboard'}
            {currentTab === 'history' && 'Historical Trends'}
            {currentTab === 'sensors' && 'Sensor Health'}
            {currentTab === 'settings' && 'Settings'}
          </h2>
          <div className="header-actions">
            <span className="last-update">
              Updated {lastUpdate.toLocaleTimeString()}
            </span>
            <button
              className="btn btn-refresh"
              onClick={handleRefresh}
              disabled={loading}
            >
              {loading ? 'Refreshing...' : '🔄 Refresh'}
            </button>
          </div>
        </header>

        {/* Error Display */}
        {error && (
          <div className="error-banner">
            <span className="error-icon">⚠️</span>
            <p>{error}</p>
          </div>
        )}

        {/* Tab Content */}
        <div className="tab-content">
          {currentTab === 'dashboard' && liveData && (
            <div className="dashboard-content">
              <LiveStatusSection data={liveData} />
              <EnvironmentalMetrics data={liveData} />
            </div>
          )}

          {currentTab === 'history' && (
            <HistoryTab apiBaseUrl={API_BASE_URL} />
          )}

          {currentTab === 'sensors' && (
            <SensorsTab
              sensorHealth={sensorHealth}
              apiBaseUrl={API_BASE_URL}
            />
          )}

          {currentTab === 'settings' && (
            <SettingsTab apiBaseUrl={API_BASE_URL} />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
