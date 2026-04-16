import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Dashboard.css';

// ─── Stat Card ───────────────────────────────────────────────────────────────
const StatCard = ({ label, value, sub, color, icon }) => (
  <div className="stat-card" style={{ borderTopColor: color }}>
    <div className="stat-card-top">
      <span className="stat-card-icon" style={{ background: `${color}20`, color }}>{icon}</span>
      <span className="stat-card-label">{label}</span>
    </div>
    <div className="stat-card-value" style={{ color }}>{value}</div>
    {sub && <div className="stat-card-sub">{sub}</div>}
  </div>
);

// ─── Occupancy ring ──────────────────────────────────────────────────────────
const OccupancyRing = ({ rate }) => {
  const r = 36, circ = 2 * Math.PI * r;
  const pct = Math.min(100, Math.max(0, rate || 0));
  const offset = circ - (pct / 100) * circ;
  const color = pct <= 40 ? '#10b981' : pct <= 75 ? '#f59e0b' : '#ef4444';
  return (
    <svg width="90" height="90" viewBox="0 0 90 90">
      <circle cx="45" cy="45" r={r} fill="none" stroke="rgba(148,163,184,.15)" strokeWidth="8"/>
      <circle cx="45" cy="45" r={r} fill="none" stroke={color} strokeWidth="8"
        strokeDasharray={circ} strokeDashoffset={offset}
        strokeLinecap="round" transform="rotate(-90 45 45)"
        style={{ transition: 'stroke-dashoffset .6s ease' }}/>
      <text x="45" y="48" textAnchor="middle" fill={color} fontSize="14" fontWeight="700">{Math.round(pct)}%</text>
    </svg>
  );
};

// ─── Dashboard ────────────────────────────────────────────────────────────────
const Dashboard = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const [cameras, setCameras]           = useState([]);
  const [selectedCamera, setSelectedCamera] = useState(null);
  const [parkingData, setParkingData]   = useState(null);
  const [loading, setLoading]           = useState(true);
  const [error, setError]               = useState(null);
  const [viewMode, setViewMode]         = useState('stream');   // 'stream' | 'frame'
  const [streamOk, setStreamOk]         = useState(true);
  const [favorites, setFavorites]       = useState([]);
  const pollingRef = useRef(null);
  const streamRef  = useRef(null);

  const getNoSlotStreamUrl = useCallback((cameraId) => {
    const base = api.parking.getStream(cameraId, { overlaySlots: false });
    return `${base}${base.includes('?') ? '&' : '?'}t=${Date.now()}`;
  }, []);

  // ── load cameras ───────────────────────────────────────────────────────────
  const loadCameras = useCallback(async () => {
    try {
      const data = await api.cameras.getAll();
      setCameras(data);

      const camIdFromState = location.state?.cameraId;
      const target = camIdFromState
        ? data.find(c => c.id === camIdFromState)
        : data[0];
      if (target) setSelectedCamera(target);
      navigate(location.pathname, { replace: true, state: {} });

      setLoading(false);
      setError(null);
    } catch (err) {
      setError('Cannot reach backend. Is it running on port 8000?');
      setLoading(false);
    }
  }, []);

  // ── load favorites ─────────────────────────────────────────────────────────
  const loadFavorites = useCallback(async () => {
    try {
      const fav = await api.cameras.getFavorites();
      setFavorites(fav.map(f => f.id));
    } catch { /* ignore */ }
  }, []);

  // ── poll parking status ────────────────────────────────────────────────────
  const loadParkingData = useCallback(async (camId) => {
    try {
      const data = await api.parking.getStatus(camId, { statusMode: 'vehicle' });
      setParkingData(data);
      setError(null);
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    loadCameras();
    loadFavorites();
  }, []);

  useEffect(() => {
    if (!selectedCamera) return;
    loadParkingData(selectedCamera.id);
    pollingRef.current = setInterval(() => loadParkingData(selectedCamera.id), 2500);
    return () => clearInterval(pollingRef.current);
  }, [selectedCamera]);

  // ── toggle favorite ─────────────────────────────────────────────────────────
  const toggleFavorite = async (camId) => {
    const isFav = favorites.includes(camId);
    try {
      if (isFav) { await api.cameras.removeFavorite(camId); setFavorites(p => p.filter(id => id !== camId)); }
      else        { await api.cameras.addFavorite(camId);   setFavorites(p => [...p, camId]); }
    } catch { /* ignore */ }
  };

  // ── derived stats ──────────────────────────────────────────────────────────
  const registeredTotal = Number(selectedCamera?.total_slots || 0);
  const apiTotal = Number(parkingData?.total_slots || 0);
  const total = registeredTotal > 0 ? registeredTotal : apiTotal;

  const predictedOccupied = Number(parkingData?.occupied_slots || 0);
  const predictedPartial = Number(parkingData?.partial_slots || 0);
  const occupied = Math.min(total, predictedOccupied);
  const partial = Math.min(Math.max(0, total - occupied), predictedPartial);
  const free = Math.max(0, total - occupied - partial);
  const rate = total > 0 ? ((occupied + partial) / total) * 100 : 0;

  const rawSlots = parkingData?.slots || [];
  const slotsForGrid = total > 0
    ? [
        ...rawSlots,
        ...Array.from({ length: Math.max(0, total - rawSlots.length) }, (_, idx) => ({
          id: rawSlots.length + idx + 1,
          status: 'free',
        })),
      ].slice(0, total)
    : rawSlots;

  if (loading) return (
    <div className="page-container loading-center">
      <div className="spinner" />
      <p>Loading dashboard…</p>
    </div>
  );

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>Parking Dashboard</h1>
          <p className="text-secondary">Real-time AI-powered parking monitoring</p>
        </div>
        <span className={`badge ${error ? 'badge-red' : 'badge-green'}`}>
          {error ? '● Offline' : '● Live'}
        </span>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Camera selector */}
      <div className="dash-camera-bar card mb-4">
        <div className="flex items-center gap-3 flex-wrap">
          <label className="text-sm text-secondary" style={{whiteSpace:'nowrap'}}>Select Camera:</label>
          <select
            className="dash-camera-select"
            value={selectedCamera?.id || ''}
            onChange={e => {
              const cam = cameras.find(c => c.id === e.target.value);
              if (cam) setSelectedCamera(cam);
            }}
          >
            <option value="">— Choose a camera —</option>
            {cameras.map(c => (
              <option key={c.id} value={c.id}>{c.name} — {c.location}</option>
            ))}
          </select>
          {selectedCamera && (
            <button
              className={`btn btn-sm ${favorites.includes(selectedCamera.id) ? 'btn-danger' : 'btn-ghost'}`}
              onClick={() => toggleFavorite(selectedCamera.id)}
              title={favorites.includes(selectedCamera.id) ? 'Remove from favorites' : 'Add to favorites'}
            >
              {favorites.includes(selectedCamera.id) ? '★ Favorited' : '☆ Add Favorite'}
            </button>
          )}
        </div>
      </div>

      {selectedCamera ? (
        <>
          {/* Stats row */}
          <div className="grid-4 mb-4">
            <StatCard label="Total Slots"   value={total}    color="#818cf8"  icon="🅿️" />
            <StatCard label="Available"     value={free}     color="#ef4444"  icon="✓"
              sub={total ? `${Math.round(free/total*100)}%` : ''} />
            <StatCard label="Partial"       value={partial}  color="#f59e0b"  icon="◑"
              sub={total ? `${Math.round(partial/total*100)}%` : ''} />
            <StatCard label="Occupied"      value={occupied} color="#10b981"  icon="✗"
              sub={total ? `${Math.round(occupied/total*100)}%` : ''} />
          </div>

          {/* Main content */}
          <div className="dash-main">
            {/* Video feed */}
            <div className="dash-video-card card">
              <div className="dash-video-header flex justify-between items-center mb-4">
                <div>
                  <h3 style={{color:'var(--text-primary)'}}>{selectedCamera.name}</h3>
                  <p className="text-sm text-secondary">{selectedCamera.location}</p>
                </div>
                <div className="flex gap-2">
                  <button
                    className={`btn btn-sm ${viewMode === 'stream' ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => { setViewMode('stream'); setStreamOk(true); }}
                  >Live</button>
                  <button
                    className={`btn btn-sm ${viewMode === 'frame' ? 'btn-primary' : 'btn-ghost'}`}
                    onClick={() => { setViewMode('frame'); setStreamOk(true); }}
                  >Frame</button>
                </div>
              </div>

              <div className="dash-video-wrap">
                {viewMode === 'stream' ? (
                  <img
                    ref={streamRef}
                    src={getNoSlotStreamUrl(selectedCamera.id)}
                    alt="Live stream"
                    className="dash-video"
                    onLoad={() => setStreamOk(true)}
                    onError={() => setStreamOk(false)}
                  />
                ) : (
                  <FramePoller cameraId={selectedCamera.id} />
                )}
                {!streamOk && viewMode === 'stream' && (
                  <div className="dash-video-overlay">
                    <p>Stream unavailable</p>
                    <button className="btn btn-primary btn-sm mt-2"
                      onClick={() => { setStreamOk(true); if(streamRef.current) streamRef.current.src = getNoSlotStreamUrl(selectedCamera.id); }}>
                      Retry
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Right panel */}
            <div className="dash-right">
              {/* Occupancy ring */}
              <div className="card dash-ring-card">
                <h4 className="text-sm text-secondary mb-4">Occupancy Rate</h4>
                <div className="flex items-center gap-4 justify-between">
                  <OccupancyRing rate={rate} />
                  <div className="flex flex-col gap-2">
                    <LegendRow color="var(--slot-free)"     label="Available" count={free} />
                    <LegendRow color="var(--slot-partial)"  label="Partial"   count={partial} />
                    <LegendRow color="var(--slot-occupied)" label="Occupied"  count={occupied} />
                  </div>
                </div>
              </div>

              {/* Slot grid */}
              <div className="card dash-slots-card">
                <h4 className="text-sm text-secondary mb-3">Slot Overview ({total})</h4>
                <SlotMiniGrid slots={slotsForGrid} />
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="dash-empty card">
          <div className="dash-empty-icon">🅿️</div>
          <h2>Select a Camera</h2>
          <p className="text-secondary">Choose a camera from the dropdown above to view real-time parking status</p>
          <button className="btn btn-primary mt-4" onClick={() => navigate('/cameras')}>+ Add Camera</button>
        </div>
      )}

      {/* Favorites quick-access */}
      {favorites.length > 0 && (
        <div className="dash-favorites mt-4">
          <h4 className="text-sm text-secondary mb-2">⭐ Favorite Areas</h4>
          <div className="flex gap-2 flex-wrap">
            {cameras.filter(c => favorites.includes(c.id)).map(c => (
              <button key={c.id} className="btn btn-ghost btn-sm" onClick={() => setSelectedCamera(c)}>
                {c.name}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Frame poller ─────────────────────────────────────────────────────────────
const FramePoller = ({ cameraId }) => {
  const [src, setSrc] = useState(null);
  useEffect(() => {
    if (!cameraId) return;
    const poll = () => {
      const base = api.parking.getFrame(cameraId, { overlaySlots: false });
      setSrc(`${base}${base.includes('?') ? '&' : '?'}t=${Date.now()}`);
    };
    poll();
    const id = setInterval(poll, 800);
    return () => clearInterval(id);
  }, [cameraId]);
  return src ? <img src={src} alt="Frame" className="dash-video" /> : <div className="loading-center"><div className="spinner"/></div>;
};

// ─── Legend row ───────────────────────────────────────────────────────────────
const LegendRow = ({ color, label, count }) => (
  <div className="flex items-center gap-2 text-sm">
    <span className="status-dot" style={{ background: color }} />
    <span className="text-secondary">{label}</span>
    <span className="font-bold" style={{ color, marginLeft: 'auto' }}>{count}</span>
  </div>
);

// ─── Mini slot grid ───────────────────────────────────────────────────────────
const SlotMiniGrid = ({ slots }) => {
  if (!slots.length) return <p className="text-sm text-muted">No slot data</p>;
  return (
    <div className="slot-mini-grid">
      {slots.map(s => (
        <div
          key={s.id}
          className={`slot-mini slot-mini-${s.status}`}
          title={`Slot #${s.id}: ${s.status}`}
        >
          <span>{s.id}</span>
        </div>
      ))}
    </div>
  );
};

export default Dashboard;

