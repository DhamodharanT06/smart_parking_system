import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import './TrailView.css';

export default function TrailView() {
  const [videos, setVideos] = useState([]);
  const [selectedVideo, setSelectedVideo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      setLoading(true);
      const data = await api.video.listTrails();
      setVideos(data.videos || []);
      setError(null);
    } catch (err) {
      setError('Failed to fetch videos');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="trail-view">
      <h2>🎬 Trail View - Test Model Performance</h2>

      <div className="trail-controls">
        <div className="video-selector">
          <label>Select Video:</label>
          <select
            value={selectedVideo || ''}
            onChange={(e) => setSelectedVideo(e.target.value)}
          >
            <option value="">-- Choose a video --</option>
            {videos.map(video => (
              <option key={video.name} value={video.name}>
                {video.name} ({video.size_mb} MB)
              </option>
            ))}
          </select>
        </div>
      </div>

      {loading && <div>Loading videos...</div>}
      {error && <div className="error">{error}</div>}

      {selectedVideo && (
        <div className="video-player">
          <video
            width="100%"
            height="auto"
            controls
            src={api.video.getTrailUrl(selectedVideo)}
          >
            Your browser does not support the video tag.
          </video>
        </div>
      )}

      {!selectedVideo && videos.length > 0 && (
        <div className="video-list">
          <h3>Available Test Videos:</h3>
          <ul>
            {videos.map(video => (
              <li key={video.name}>
                <button onClick={() => setSelectedVideo(video.name)}>
                  ▶ {video.name} ({video.size_mb} MB)
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
