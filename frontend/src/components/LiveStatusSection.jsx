import React from 'react';

export default function LiveStatusSection({ data }) {
  if (!data || !data.live_status) {
    return <div className="live-status">Loading...</div>;
  }

  const { people_count, estimated_wait_time, advisory_message } = data.live_status;

  // Determine advisory color and urgency
  let advisoryClass = 'advisory-neutral';
  if (people_count <= 3) {
    advisoryClass = 'advisory-good';
  } else if (people_count <= 7) {
    advisoryClass = 'advisory-moderate';
  } else {
    advisoryClass = 'advisory-busy';
  }

  return (
    <section className="live-status-section">
      <h3 className="section-title">Live Status</h3>

      {/* Advisory Message - Most Prominent */}
      <div className={`advisory-box ${advisoryClass}`}>
        <div className="advisory-icon">💬</div>
        <div className="advisory-content">
          <h4>Advisory Message</h4>
          <p className="advisory-text">{advisory_message}</p>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="metrics-grid">
        {/* People Count */}
        <div className="metric-card metric-large">
          <div className="metric-header">
            <h4>People in Queue</h4>
            <span className="metric-icon">👥</span>
          </div>
          <div className="metric-value">
            <span className="large-number">{people_count}</span>
            <span className="metric-unit">people</span>
          </div>
          <div className="metric-bar">
            <div
              className="metric-bar-fill"
              style={{
                width: Math.min((people_count / 15) * 100, 100) + '%',
              }}
            ></div>
          </div>
        </div>

        {/* Estimated Wait Time */}
        <div className="metric-card metric-large">
          <div className="metric-header">
            <h4>Est. Wait Time</h4>
            <span className="metric-icon">⏱️</span>
          </div>
          <div className="metric-value">
            <span className="large-number">{estimated_wait_time}</span>
            <span className="metric-unit">min</span>
          </div>
          <div className="metric-description">
            Based on {people_count} person{people_count !== 1 ? 's' : ''}
          </div>
        </div>
      </div>
    </section>
  );
}
