import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import './CameraSelector.css';

export default function CameraSelector({ onCameraSelect, selectedCameraId }) {
  const [cameras, setCameras] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const cacheRef = useRef({ data: null, timestamp: null });
  const CACHE_DURATION = 30000; // 30 seconds

  useEffect(() => {
    fetchCameras();
  }, []);

  const fetchCameras = async () => {
    try {
      // Check cache
      const now = Date.now();
      if (cacheRef.current.data && (now - cacheRef.current.timestamp) < CACHE_DURATION) {
        setCameras(cacheRef.current.data);
        setLoading(false);
        return;
      }

      setLoading(true);
      const data = await api.cameras.getAll();
      
      // Cache the result
      cacheRef.current = {
        data: data,
        timestamp: now
      };
      
      setCameras(data);
      setError(null);
    } catch (err) {
      const errorMsg = err.message || 'Failed to fetch cameras';
      setError(errorMsg);
      console.error('Camera fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return (
    <div className="camera-selector loading">
      <div className="loading-icon">⏳</div>
      <div>Loading cameras...</div>
    </div>
  );
  if (error) return (
    <div className="camera-selector error">
      <div className="error-icon">⚠️</div>
      <div className="error-message">{error}</div>
      <button onClick={fetchCameras} className="retry-btn">🔄 Retry</button>
    </div>
  );

  return (
    <div className="camera-selector">
      <h2>📹 Cameras</h2>
      <div className="camera-grid">
        {cameras.map(camera => (
          <div
            key={camera.id}
            className={`camera-card ${selectedCameraId === camera.id ? 'active' : ''}`}
            onClick={() => onCameraSelect(camera.id)}
          >
            <div className="camera-name">{camera.name}</div>
            <div className="camera-location">📍 {camera.location}</div>
            <div className="camera-status">
              <span className={`status-indicator ${camera.status}`}></span>
              <span>{camera.status}</span>
            </div>
            {camera.distance_km && (
              <div className="camera-distance">📊 {camera.distance_km} km away</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
