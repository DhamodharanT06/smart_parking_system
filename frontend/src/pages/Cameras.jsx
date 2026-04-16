import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './Cameras.css';

/* ─── Source type helper ─────────────────────────────────────── */
const SOURCE_TYPES = [
  { value: 'file',    label: 'Video File',      placeholder: 'parking_video.mp4 or C:/path/to/video.mp4' },
  { value: 'webcam',  label: 'Webcam',           placeholder: '0  (camera index, default is 0)' },
  { value: 'rtsp',    label: 'RTSP / IP Camera', placeholder: 'rtsp://user:pass@192.168.1.10:554/stream' },
  { value: 'http',    label: 'HTTP / MJPEG',     placeholder: 'http://192.168.1.10:8080/video' },
];

const SOURCE_HINT = {
  file:   'Place the video file inside the backend/ folder, or provide the full path.',
  webcam: 'Connect a USB/built-in camera. Index 0 is usually the default camera.',
  rtsp:   'Use rtsp://username:password@ip:port/path. Leave blank auth if not needed.',
  http:   'Supports MJPEG streams like those from IP cameras or phone apps.',
};

/* ─── Camera type badge ──────────────────────────────────────── */
const TypeBadge = ({ type }) => {
  const map = { file: 'badge-blue', webcam: 'badge-green', rtsp: 'badge-orange', http: 'badge-orange', unknown: 'badge-red' };
  return <span className={`badge ${map[type] || 'badge-blue'}`}>{type || 'file'}</span>;
};

/* ─── Camera card ────────────────────────────────────────────── */
const CameraCard = ({ camera, onSelect, selected, onFav, isFav, onDelete, onEdit }) => (
  <div className={`camera-card ${selected ? 'selected' : ''}`} onClick={() => onSelect(camera)}>
    <div className="camera-card-header">
      <div className="camera-card-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2"/>
        </svg>
      </div>
      <div className="camera-card-info">
        <span className="camera-card-name">{camera.name}</span>
        <span className="camera-card-loc text-secondary text-xs">{camera.location}</span>
      </div>
      <button className="btn-icon btn" onClick={e => { e.stopPropagation(); onFav(camera.id); }}
        title={isFav ? 'Remove favorite' : 'Add to favorites'}>
        {isFav ? '★' : '☆'}
      </button>
    </div>
    <div className="camera-card-meta">
      <TypeBadge type={camera.camera_type} />
      <span className={`badge ${camera.status === 'active' ? 'badge-green' : 'badge-orange'}`}>
        {camera.status}
      </span>
      {camera.total_slots > 0 && (
        <span className="badge badge-blue">{camera.total_slots} slots</span>
      )}
    </div>
    <div className="camera-card-source text-xs text-muted">{camera.video_source}</div>
    <div className="camera-card-actions">
      <button className="btn btn-primary btn-sm" onClick={e => { e.stopPropagation(); onSelect(camera, true); }}>
        View
      </button>
      <button className="btn btn-ghost btn-sm" onClick={e => { e.stopPropagation(); onEdit(camera); }}>
        Edit
      </button>
      <button className="btn btn-danger btn-sm" onClick={e => { e.stopPropagation(); onDelete(camera.id); }}>
        Delete
      </button>
    </div>
  </div>
);

/* ─── Add Camera Form ────────────────────────────────────────── */
const AddCameraForm = ({ initialCamera, onSaved, onCancel }) => {
  const [form, setForm] = useState({ name: '', location: '', sourceType: 'file', video_source: '', latitude: '', longitude: '', username: '', password: '', total_slots: '' });
  const [saving, setSaving] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!initialCamera) {
      setForm({ name: '', location: '', sourceType: 'file', video_source: '', latitude: '', longitude: '', username: '', password: '', total_slots: '' });
      return;
    }
    const src = (initialCamera.camera_type || '').toLowerCase();
    const inferredType = ['file', 'webcam', 'rtsp', 'http'].includes(src)
      ? src
      : (initialCamera.video_source?.match(/^\d+$/) ? 'webcam' : (initialCamera.video_source?.startsWith('rtsp') ? 'rtsp' : (initialCamera.video_source?.startsWith('http') ? 'http' : 'file')));

    setForm({
      name: initialCamera.name || '',
      location: initialCamera.location || '',
      sourceType: inferredType,
      video_source: initialCamera.video_source || '',
      latitude: initialCamera.latitude ?? '',
      longitude: initialCamera.longitude ?? '',
      username: initialCamera.username || '',
      password: initialCamera.password || '',
      total_slots: initialCamera.total_slots ?? '',
    });
  }, [initialCamera]);

  const src = SOURCE_TYPES.find(s => s.value === form.sourceType);

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));

  const handleSave = async () => {
    if (!form.name.trim() || !form.video_source.trim()) {
      setError('Name and source are required.'); return;
    }
    setSaving(true); setError('');
    try {
      if (initialCamera?.id) {
        await api.cameras.update(initialCamera.id, {
          name: form.name,
          location: form.location,
          video_source: form.video_source,
          latitude: form.latitude ? parseFloat(form.latitude) : null,
          longitude: form.longitude ? parseFloat(form.longitude) : null,
          username: form.username || null,
          password: form.password || null,
          total_slots: form.total_slots === '' ? 0 : Math.max(0, parseInt(form.total_slots, 10) || 0),
        });
      } else {
        await api.cameras.add({
          name: form.name,
          location: form.location,
          video_source: form.video_source,
          latitude: form.latitude ? parseFloat(form.latitude) : null,
          longitude: form.longitude ? parseFloat(form.longitude) : null,
          username: form.username || null,
          password: form.password || null,
          total_slots: form.total_slots === '' ? 0 : Math.max(0, parseInt(form.total_slots, 10) || 0),
        });
      }
      setForm({ name: '', location: '', sourceType: 'file', video_source: '', latitude: '', longitude: '', username: '', password: '', total_slots: '' });
      setTestResult(null);
      onSaved();
    } catch (e) {
      setError(e.message || 'Failed to save camera');
    } finally { setSaving(false); }
  };

  return (
    <div className="add-camera-form card">
      <h3 className="form-title">{initialCamera?.id ? 'Edit Camera' : 'Add New Camera / Video Source'}</h3>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="form-grid">
        <div className="form-group">
          <label>Camera Name *</label>
          <input placeholder="e.g. Main Entrance" value={form.name} onChange={e => set('name', e.target.value)} />
        </div>
        <div className="form-group">
          <label>Location</label>
          <input placeholder="e.g. Building A – Level 1" value={form.location} onChange={e => set('location', e.target.value)} />
        </div>
      </div>

      <div className="form-grid">
        <div className="form-group">
          <label>Number of Slots *</label>
          <input type="number" min={0} placeholder="e.g. 12" value={form.total_slots} onChange={e => set('total_slots', e.target.value)} />
        </div>
      </div>

      {/* Source type selector */}
      <div className="form-group">
        <label>Source Type</label>
        <div className="source-type-grid">
          {SOURCE_TYPES.map(s => (
            <button
              key={s.value}
              className={`source-type-btn ${form.sourceType === s.value ? 'active' : ''}`}
              onClick={() => set('sourceType', s.value)}
            >{s.label}</button>
          ))}
        </div>
        <p className="form-hint">{SOURCE_HINT[form.sourceType]}</p>
      </div>

      <div className="form-group">
        <label>Video / Camera Source *</label>
        <input placeholder={src?.placeholder} value={form.video_source} onChange={e => set('video_source', e.target.value)} />
      </div>

      {/* RTSP / HTTP credentials */}
      {(form.sourceType === 'rtsp' || form.sourceType === 'http') && (
        <div className="form-grid">
          <div className="form-group">
            <label>Username (optional)</label>
            <input placeholder="admin" value={form.username} onChange={e => set('username', e.target.value)} />
          </div>
          <div className="form-group">
            <label>Password (optional)</label>
            <input type="password" placeholder="••••••" value={form.password} onChange={e => set('password', e.target.value)} />
          </div>
        </div>
      )}

      <div className="form-grid">
        <div className="form-group">
          <label>Latitude (for distance search)</label>
          <input type="number" step="any" placeholder="e.g. 13.0827" value={form.latitude} onChange={e => set('latitude', e.target.value)} />
        </div>
        <div className="form-group">
          <label>Longitude</label>
          <input type="number" step="any" placeholder="e.g. 80.2707" value={form.longitude} onChange={e => set('longitude', e.target.value)} />
        </div>
      </div>

      {testResult && (
        <div className={`alert ${testResult.ok ? 'alert-success' : 'alert-error'}`}>
          {testResult.message}
        </div>
      )}

      <div className="flex gap-2 mt-4">
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? 'Saving…' : (initialCamera?.id ? 'Update Camera' : '+ Add Camera')}
        </button>
        {initialCamera?.id && (
          <button className="btn btn-ghost" onClick={onCancel} disabled={saving}>
            Cancel Edit
          </button>
        )}
      </div>
    </div>
  );
};

/* ─── Nearby search ──────────────────────────────────────────── */
const NearbySearch = ({ onSelect }) => {
  const [lat, setLat] = useState('');
  const [lon, setLon] = useState('');
  const [radius, setRadius] = useState(5);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [located, setLocated] = useState(false);

  const locate = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(p => {
      setLat(p.coords.latitude.toFixed(6));
      setLon(p.coords.longitude.toFixed(6));
      setLocated(true);
    });
  };

  const search = async () => {
    if (!lat || !lon) return;
    setLoading(true);
    try {
      const data = await api.cameras.getNearby(parseFloat(lat), parseFloat(lon), radius);
      setResults(data);
    } catch { setResults([]); }
    finally { setLoading(false); }
  };

  return (
    <div className="nearby-search card">
      <h3 className="form-title">🗺 Find Nearby Parking Areas</h3>
      <div className="form-grid">
        <div className="form-group">
          <label>Latitude</label>
          <input placeholder="13.0827" value={lat} onChange={e => setLat(e.target.value)} />
        </div>
        <div className="form-group">
          <label>Longitude</label>
          <input placeholder="80.2707" value={lon} onChange={e => setLon(e.target.value)} />
        </div>
        <div className="form-group">
          <label>Radius (km)</label>
          <input type="number" min={0.5} max={50} value={radius} onChange={e => setRadius(e.target.value)} />
        </div>
      </div>
      <div className="flex gap-2">
        <button className="btn btn-ghost btn-sm" onClick={locate}>📍 Use My Location</button>
        <button className="btn btn-primary btn-sm" onClick={search} disabled={loading || !lat || !lon}>
          {loading ? 'Searching…' : 'Search'}
        </button>
      </div>
      {results.length > 0 && (
        <div className="nearby-results">
          {results.map(c => (
            <div key={c.id} className="nearby-item" onClick={() => onSelect(c)}>
              <span className="nearby-name">{c.name}</span>
              <span className="text-xs text-secondary">{c.location}</span>
              {c.distance_km != null && (
                <span className="badge badge-blue">{c.distance_km} km</span>
              )}
            </div>
          ))}
        </div>
      )}
      {results.length === 0 && located && <p className="text-sm text-muted mt-2">No cameras found within {radius}km.</p>}
    </div>
  );
};

/* ─── Main Component ─────────────────────────────────────────── */
const Cameras = () => {
  const navigate = useNavigate();
  const [cameras, setCameras]   = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [selected, setSelected] = useState(null);
  const [tab, setTab]           = useState('all'); // 'all' | 'favorites' | 'add' | 'nearby'
  const [editingCamera, setEditingCamera] = useState(null);

  const load = useCallback(async () => {
    try {
      const [cams, favs] = await Promise.allSettled([
        api.cameras.getAll(),
        api.cameras.getFavorites(),
      ]);
      if (cams.status === 'fulfilled')  setCameras(cams.value);
      if (favs.status === 'fulfilled')  setFavorites(favs.value.map(f => f.id));
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const toggleFav = async (id) => {
    const isFav = favorites.includes(id);
    try {
      if (isFav) { await api.cameras.removeFavorite(id); setFavorites(p => p.filter(x => x !== id)); }
      else        { await api.cameras.addFavorite(id);   setFavorites(p => [...p, id]); }
    } catch { /* ignore */ }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this camera?')) return;
    try { await api.cameras.delete(id); load(); } catch { /* ignore */ }
  };

  const handleSelect = (cam, go) => {
    setSelected(cam);
    if (go) navigate('/', { state: { cameraId: cam.id } });
  };

  const shown = tab === 'favorites' ? cameras.filter(c => favorites.includes(c.id)) : cameras;

  return (
    <div className="page-container">
      <div className="page-header flex justify-between items-center">
        <div><h1>Camera Management</h1><p className="text-secondary">Add, manage, and monitor your parking cameras</p></div>
        <span className="badge badge-blue">{cameras.length} cameras</span>
      </div>

      {/* Tab bar */}
      <div className="tab-bar card mb-4">
        {['all', 'favorites', 'add', 'nearby'].map(t => (
          <button key={t} className={`tab-btn ${tab === t ? 'active' : ''}`} onClick={() => {
            if (t === 'add') setEditingCamera(null);
            setTab(t);
          }}>
            {{ all: '📹 All Cameras', favorites: '⭐ Favorites', add: '+ Add Camera', nearby: '🗺 Nearby' }[t]}
          </button>
        ))}
      </div>

      {tab === 'add' && (
        <AddCameraForm
          initialCamera={editingCamera}
          onSaved={() => { setEditingCamera(null); load(); setTab('all'); }}
          onCancel={() => { setEditingCamera(null); setTab('all'); }}
        />
      )}
      {tab === 'nearby' && <NearbySearch onSelect={c => { setSelected(c); setTab('all'); navigate('/', { state: { cameraId: c.id } }); }} />}

      {(tab === 'all' || tab === 'favorites') && (
        loading ? (
          <div className="loading-center"><div className="spinner"/></div>
        ) : shown.length === 0 ? (
          <div className="dash-empty card">
            <div className="dash-empty-icon">{tab === 'favorites' ? '⭐' : '📹'}</div>
            <h2>{tab === 'favorites' ? 'No Favorites Yet' : 'No Cameras Added'}</h2>
            <p className="text-secondary">
              {tab === 'favorites' ? 'Star cameras from the All Cameras tab.' : 'Add a camera or video source to get started.'}
            </p>
            <button className="btn btn-primary mt-4" onClick={() => setTab('add')}>+ Add Camera</button>
          </div>
        ) : (
          <div className="cameras-grid">
            {shown.map(c => (
              <CameraCard
                key={c.id} camera={c} selected={selected?.id === c.id}
                onSelect={handleSelect} onFav={toggleFav}
                isFav={favorites.includes(c.id)} onDelete={handleDelete}
                onEdit={(cam) => { setEditingCamera(cam); setTab('add'); }}
              />
            ))}
          </div>
        )
      )}
    </div>
  );
};

export default Cameras;
