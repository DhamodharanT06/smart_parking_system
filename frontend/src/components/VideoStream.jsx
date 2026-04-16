import React, { useState, useEffect, useRef } from 'react';
import './VideoStream.css';

const API_BASE = 'http://localhost:8000/api';

export default function VideoStream({ cameraId, onError }) {
  const [viewMode, setViewMode] = useState('stream'); // 'stream' or 'frame'
  const [streamStatus, setStreamStatus] = useState('loading'); // 'loading' | 'live' | 'error'
  const streamImgRef = useRef(null);
  const frameTimerRef = useRef(null);
  const frameImgRef = useRef(null);

  // ── STREAM MODE: set src once, browser drives the MJPEG ──────────────────
  useEffect(() => {
    if (!cameraId || viewMode !== 'stream') return;
    const img = streamImgRef.current;
    if (!img) return;

    setStreamStatus('loading');

    const streamUrl = `${API_BASE}/parking/${cameraId}/stream`;

    let retries = 0;
    const MAX_RETRIES = 3;

    const connect = () => {
      img.onload = () => {
        setStreamStatus('live');
        retries = 0;
      };
      img.onerror = () => {
        retries += 1;
        if (retries <= MAX_RETRIES) {
          setTimeout(connect, 2000);
        } else {
          setStreamStatus('error');
          if (onError) onError();
        }
      };
      // Append t= only to bust browser cache on reconnect
      img.src = `${streamUrl}?t=${Date.now()}`;
    };

    connect();

    return () => {
      img.onload = null;
      img.onerror = null;
      img.src = '';
    };
  }, [cameraId, viewMode, onError]);

  // ── FRAME MODE: poll /frame endpoint every 500 ms ─────────────────────────
  useEffect(() => {
    if (!cameraId || viewMode !== 'frame') return;
    const img = frameImgRef.current;
    if (!img) return;

    let active = true;
    let failCount = 0;
    setStreamStatus('loading');

    const loadFrame = () => {
      if (!active) return;
      const url = `${API_BASE}/parking/${cameraId}/frame?t=${Date.now()}`;
      img.onload = () => {
        if (!active) return;
        setStreamStatus('live');
        failCount = 0;
        frameTimerRef.current = setTimeout(loadFrame, 500);
      };
      img.onerror = () => {
        if (!active) return;
        failCount += 1;
        if (failCount > 4) {
          setStreamStatus('error');
          if (onError) onError();
        } else {
          frameTimerRef.current = setTimeout(loadFrame, 1500);
        }
      };
      img.src = url;
    };

    loadFrame();

    return () => {
      active = false;
      clearTimeout(frameTimerRef.current);
      if (img) { img.onload = null; img.onerror = null; }
    };
  }, [cameraId, viewMode, onError]);

  const handleRetry = () => {
    setStreamStatus('loading');
    // toggle to force useEffect to re-run
    setViewMode(v => {
      const same = v;
      return same === 'stream' ? 'frame' : 'stream';
    });
    setTimeout(() => setViewMode(v => v === 'stream' ? 'frame' : 'stream'), 50);
  };

  if (!cameraId) {
    return (
      <div className="video-stream-placeholder">
        <div className="placeholder-icon">📹</div>
        <p>Select a camera to view live detection</p>
      </div>
    );
  }

  return (
    <div className="video-stream-container">
      <div className="video-header">
        <div className="header-left">
          <h3>Live Detection</h3>
          <div className={`status-indicator ${streamStatus === 'error' ? 'error' : streamStatus === 'loading' ? 'warning' : 'active'}`}>
            <span className="status-dot"></span>
            {streamStatus === 'error' ? 'Offline' : streamStatus === 'loading' ? 'Connecting...' : 'Live'}
          </div>
        </div>
        <div className="view-toggle">
          <button
            className={`toggle-btn ${viewMode === 'stream' ? 'active' : ''}`}
            onClick={() => { setViewMode('stream'); setStreamStatus('loading'); }}
            title="Continuous MJPEG stream with YOLO detection"
          >
            📹 Stream
          </button>
          <button
            className={`toggle-btn ${viewMode === 'frame' ? 'active' : ''}`}
            onClick={() => { setViewMode('frame'); setStreamStatus('loading'); }}
            title="Polled JPEG frames with YOLO detection"
          >
            🖼️ Frames
          </button>
        </div>
      </div>

      <div className="video-wrapper">
        {streamStatus === 'loading' && (
          <div className="stream-loading">
            <div className="loading-spinner"></div>
            <p>Connecting to detection stream...</p>
          </div>
        )}

        {streamStatus === 'error' ? (
          <div className="stream-error">
            <div className="error-icon">⚠️</div>
            <p>Unable to load video</p>
            <p className="error-detail">Make sure the backend is running on port 8000</p>
            <button onClick={handleRetry} className="retry-btn">Retry</button>
          </div>
        ) : (
          <>
            {/* MJPEG stream image — always in DOM but hidden when in frame mode */}
            <img
              ref={streamImgRef}
              alt="Live Detection Stream"
              className="video-stream"
              style={{ display: viewMode === 'stream' && streamStatus === 'live' ? 'block' : 'none' }}
            />
            {/* Polled frame image */}
            <img
              ref={frameImgRef}
              alt="Detection Frame"
              className="video-stream"
              style={{ display: viewMode === 'frame' && streamStatus === 'live' ? 'block' : 'none' }}
            />
          </>
        )}
      </div>
    </div>
  );
}
