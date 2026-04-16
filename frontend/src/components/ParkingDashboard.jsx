import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import './ParkingDashboard.css';

export default function ParkingDashboard({ cameraId }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshInterval, setRefreshInterval] = useState(5); // seconds - increased from 3
  const intervalRef = useRef(null);
  const lastFetchRef = useRef(null);

  useEffect(() => {
    if (!cameraId) return;

    const fetchStatus = async () => {
      try {
        const data = await api.parking.getStatus(cameraId);
        setStatus(data);
        setError(null);
        lastFetchRef.current = Date.now();
      } catch (err) {
        const errorMsg = err.message || 'Failed to fetch parking status';
        setError(errorMsg);
        console.error('Parking status error:', err);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    setLoading(true);
    fetchStatus();
    
    // Set up interval
    if (intervalRef.current) clearInterval(intervalRef.current);
    
    intervalRef.current = setInterval(() => {
      // Only fetch if not currently loading
      if (!loading) {
        fetchStatus();
      }
    }, refreshInterval * 1000);
    
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [cameraId, refreshInterval]);

  if (!cameraId) return <div className="dashboard">Select a camera to view parking status</div>;
  if (loading) return <div className="dashboard loading">⏳ Loading parking data...</div>;
  if (error) return (
    <div className="dashboard error">
      <div className="error-icon">⚠️</div>
      <div className="error-message">{error}</div>
      <button onClick={() => window.location.reload()} className="retry-btn">🔄 Retry</button>
    </div>
  );
  if (!status) return <div className="dashboard">No data available</div>;

  const occupancyPercentage = Math.round(status.occupancy_rate);
  const availabilityPercentage = 100 - occupancyPercentage;

  return (
    <div className="parking-dashboard">
      <div className="dashboard-header">
        <h2>📊 {status.camera_name}</h2>
        <div className="refresh-control">
          <label>Refresh interval:</label>
          <select value={refreshInterval} onChange={(e) => setRefreshInterval(Number(e.target.value))}>
            <option value={1}>1 second</option>
            <option value={3}>3 seconds</option>
            <option value={5}>5 seconds</option>
            <option value={10}>10 seconds</option>
          </select>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card total">
          <div className="stat-icon">🅿️</div>
          <div className="stat-value">{status.total_slots}</div>
          <div className="stat-label">Total Slots</div>
        </div>

        <div className="stat-card available">
          <div className="stat-icon">✅</div>
          <div className="stat-value">{status.available_slots}</div>
          <div className="stat-label">Available</div>
        </div>

        <div className="stat-card occupied">
          <div className="stat-icon">🚗</div>
          <div className="stat-value">{status.occupied_slots}</div>
          <div className="stat-label">Occupied</div>
        </div>

        <div className="stat-card occupancy">
          <div className="stat-value">{occupancyPercentage}%</div>
          <div className="stat-label">Occupancy Rate</div>
        </div>
      </div>

      <div className="occupancy-chart">
        <div className="chart-title">Occupancy Overview</div>
        <div className="chart-bars">
          <div className="bar">
            <div className="bar-fill occupied-bar" style={{ width: `${occupancyPercentage}%` }}></div>
            <div className="bar-label">Occupied: {occupancyPercentage}%</div>
          </div>
          <div className="bar">
            <div className="bar-fill available-bar" style={{ width: `${availabilityPercentage}%` }}></div>
            <div className="bar-label">Available: {availabilityPercentage}%</div>
          </div>
        </div>
      </div>

      <div className="timestamp">Last updated: {new Date(status.timestamp).toLocaleTimeString()}</div>
    </div>
  );
}
