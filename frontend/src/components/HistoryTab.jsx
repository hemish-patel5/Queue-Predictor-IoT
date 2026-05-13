import React, { useState, useEffect, useRef } from "react";
import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import "chartjs-adapter-date-fns";

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  CategoryScale,
  Title,
  Tooltip,
  Legend,
);

export default function HistoryTab({ apiBaseUrl }) {
  // default to 7 days (168 hours)
  const [hours, setHours] = useState(168);
  const [loading, setLoading] = useState(true);
  const queueChartRef = useRef(null);
  const envChartRef = useRef(null);
  const queueChartInstance = useRef(null);
  const envChartInstance = useRef(null);

  const fetchAndRender = async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${apiBaseUrl}/api/v1/history?hours=${hours}&limit=10000`,
      );
      if (!res.ok) throw new Error("Failed to fetch history");
      const data = await res.json();

      // Prepare datasets: ensure numeric y values where possible
      const mapPoints = (arr) =>
        (arr || []).map((p) => ({
          x: p.ts,
          y:
            p.value === null
              ? null
              : isNaN(Number(p.value))
                ? p.value
                : Number(p.value),
        }));

      const queueData = mapPoints(data.queue_history);
      const tempData = mapPoints(data.temperature_history);
      const gasData = mapPoints(data.gas_history);
      const soundData = mapPoints(data.sound_history);

      // compute x-axis window based on selected hours
      const nowMs = Date.now();
      let startMs = nowMs - hours * 60 * 60 * 1000;
      if (hours === 0) {
        // For "All time", find the earliest timestamp across all datasets
        const allTimestamps = [
          ...queueData.map((p) => p.x),
          ...tempData.map((p) => p.x),
          ...gasData.map((p) => p.x),
          ...soundData.map((p) => p.x),
        ].filter((ts) => ts != null);
        startMs =
          allTimestamps.length > 0
            ? Math.min(...allTimestamps)
            : nowMs - 7 * 24 * 60 * 60 * 1000; // fallback to 7 days ago
      }
      const timeUnit = hours <= 1 ? "minute" : hours <= 24 ? "hour" : "day";

      // Initialize or update queue chart
      if (!queueChartInstance.current) {
        queueChartInstance.current = new Chart(queueChartRef.current, {
          type: "line",
          data: {
            datasets: [
              {
                label: "People in Frame",
                data: queueData,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59,130,246,0.2)",
                tension: 0.2,
                parsing: false,
              },
            ],
          },
          options: {
            animation: false,
            scales: {
              x: {
                type: "time",
                time: { unit: timeUnit },
                min: startMs,
                max: nowMs,
                title: { display: true, text: "Time" },
              },
              y: { beginAtZero: true, title: { display: true, text: "Count" } },
            },
          },
        });
      } else {
        queueChartInstance.current.data.datasets[0].data = queueData;
        // update x-axis window and unit
        if (
          queueChartInstance.current.options &&
          queueChartInstance.current.options.scales &&
          queueChartInstance.current.options.scales.x
        ) {
          queueChartInstance.current.options.scales.x.time.unit = timeUnit;
          queueChartInstance.current.options.scales.x.min = startMs;
          queueChartInstance.current.options.scales.x.max = nowMs;
        }
        queueChartInstance.current.update("none");
      }

      // Initialize or update env chart (temp, co2, sound)
      if (!envChartInstance.current) {
        envChartInstance.current = new Chart(envChartRef.current, {
          type: "line",
          data: {
            datasets: [
              {
                label: "Temperature (°C)",
                data: tempData,
                borderColor: "#ef4444",
                backgroundColor: "rgba(239,68,68,0.15)",
                parsing: false,
              },
              {
                label: "CO₂ (ppm)",
                data: gasData,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59,130,246,0.15)",
                parsing: false,
              },
              {
                label: "Sound",
                data: soundData,
                borderColor: "#10b981",
                backgroundColor: "rgba(16,185,129,0.15)",
                parsing: false,
              },
            ],
          },
          options: {
            animation: false,
            scales: {
              x: {
                type: "time",
                time: { unit: timeUnit },
                min: startMs,
                max: nowMs,
                title: { display: true, text: "Time" },
              },
              y: { beginAtZero: true, title: { display: true, text: "Value" } },
            },
          },
        });
      } else {
        envChartInstance.current.data.datasets[0].data = tempData;
        envChartInstance.current.data.datasets[1].data = gasData;
        envChartInstance.current.data.datasets[2].data = soundData;
        if (
          envChartInstance.current.options &&
          envChartInstance.current.options.scales &&
          envChartInstance.current.options.scales.x
        ) {
          envChartInstance.current.options.scales.x.time.unit = timeUnit;
          envChartInstance.current.options.scales.x.min = startMs;
          envChartInstance.current.options.scales.x.max = nowMs;
        }
        envChartInstance.current.update("none");
      }
    } catch (err) {
      console.error("Error fetching history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAndRender();

    // Refresh charts every 2 minutes (120000 ms)
    const interval = setInterval(fetchAndRender, 120000);
    return () => clearInterval(interval);
  }, [hours, apiBaseUrl]);

  return (
    <div className="history-tab">
      <div className="history-controls">
        <label htmlFor="hours-select">Show data for last:</label>
        <select
          id="hours-select"
          value={hours}
          onChange={(e) => setHours(parseInt(e.target.value))}
          style={{ color: "black" }}
        >
          <option value={0}>All time</option>
          <option value={1}>1 hour</option>
          <option value={3}>3 hours</option>
          <option value={6}>6 hours</option>
          <option value={12}>12 hours</option>
          <option value={24}>24 hours</option>
          <option value={48}>2 days</option>
          <option value={72}>3 days</option>
          <option value={96}>4 days</option>
          <option value={120}>5 days</option>
          <option value={144}>6 days</option>
          <option value={168}>7 days</option>
        </select>
      </div>

      <div className="history-content">
        <div className="history-chart">
          <h3>Queue History</h3>
          <canvas ref={queueChartRef} height={180} />
          {loading && <p className="chart-loading">Loading chart...</p>}
        </div>

        <div className="history-chart">
          <h3>Environmental Conditions</h3>
          <canvas ref={envChartRef} height={180} />
          {loading && <p className="chart-loading">Loading chart...</p>}
          <div className="chart-legend">
            <span style={{ color: "#ef4444" }}>— Temperature</span>
            <span style={{ color: "#3b82f6" }}>— CO₂ Level</span>
            <span style={{ color: "#10b981" }}>— Sound Level</span>
          </div>
        </div>
      </div>
    </div>
  );
}
