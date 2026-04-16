import React, { useState } from 'react';
import './Settings.css';

const ToggleSwitch = ({ checked, onChange }) => (
  <label className="toggle">
    <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)} />
    <span className="toggle-track"><span className="toggle-thumb"/></span>
  </label>
);

const Settings = () => {
  const [settings, setSettings] = useState({
    theme: 'dark',
    autoRefresh: true,
    refreshInterval: 2,
    notifications: true,
    detectionConf: 0.2,
    yoloEvery: 3,
    jpegQuality: 85,
  });
  const [saved, setSaved] = useState(false);

  const set = (k, v) => setSettings(p => ({ ...p, [k]: v }));

  const save = () => {
    localStorage.setItem('parkSenseSettings', JSON.stringify(settings));
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Settings</h1>
        <p className="text-secondary">Configure the Smart Parking System preferences</p>
      </div>

      {saved && <div className="alert alert-success">✓ Settings saved successfully</div>}

      {/* Display */}
      <div className="card settings-section">
        <h3 className="settings-section-title">Display</h3>
        <div className="settings-row">
          <div>
            <p className="settings-label">Theme</p>
            <p className="text-xs text-muted">Choose light or dark color scheme</p>
          </div>
          <div className="flex gap-2">
            {['dark', 'light'].map(t => (
              <button key={t} className={`btn btn-sm ${settings.theme === t ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => set('theme', t)}>
                {t === 'dark' ? '🌙 Dark' : '☀ Light'}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Polling */}
      <div className="card settings-section">
        <h3 className="settings-section-title">Live Updates</h3>
        <div className="settings-row">
          <div>
            <p className="settings-label">Auto Refresh</p>
            <p className="text-xs text-muted">Continuously poll parking status</p>
          </div>
          <ToggleSwitch checked={settings.autoRefresh} onChange={v => set('autoRefresh', v)} />
        </div>
        <div className="settings-row">
          <div>
            <p className="settings-label">Refresh Interval</p>
            <p className="text-xs text-muted">Seconds between status polls (1–10)</p>
          </div>
          <div className="range-group">
            <input type="range" min={1} max={10} value={settings.refreshInterval}
              onChange={e => set('refreshInterval', Number(e.target.value))} />
            <span className="range-val">{settings.refreshInterval}s</span>
          </div>
        </div>
        <div className="settings-row">
          <div>
            <p className="settings-label">Notifications</p>
            <p className="text-xs text-muted">Alert when lot reaches capacity</p>
          </div>
          <ToggleSwitch checked={settings.notifications} onChange={v => set('notifications', v)} />
        </div>
      </div>

      {/* Detection */}
      <div className="card settings-section">
        <h3 className="settings-section-title">Detection Engine (YOLO)</h3>
        <div className="settings-row">
          <div>
            <p className="settings-label">Confidence Threshold</p>
            <p className="text-xs text-muted">Minimum vehicle detection confidence (0.1 – 0.9)</p>
          </div>
          <div className="range-group">
            <input type="range" min={0.1} max={0.9} step={0.05} value={settings.detectionConf}
              onChange={e => set('detectionConf', Number(e.target.value))} />
            <span className="range-val">{settings.detectionConf.toFixed(2)}</span>
          </div>
        </div>
        <div className="settings-row">
          <div>
            <p className="settings-label">YOLO Every N Frames</p>
            <p className="text-xs text-muted">Run detection every N video frames (1 = every frame, slower)</p>
          </div>
          <div className="range-group">
            <input type="range" min={1} max={10} value={settings.yoloEvery}
              onChange={e => set('yoloEvery', Number(e.target.value))} />
            <span className="range-val">{settings.yoloEvery}</span>
          </div>
        </div>
        <div className="settings-row">
          <div>
            <p className="settings-label">JPEG Quality</p>
            <p className="text-xs text-muted">Stream image quality (50–100)</p>
          </div>
          <div className="range-group">
            <input type="range" min={50} max={100} value={settings.jpegQuality}
              onChange={e => set('jpegQuality', Number(e.target.value))} />
            <span className="range-val">{settings.jpegQuality}</span>
          </div>
        </div>
      </div>

      {/* About */}
      <div className="card settings-section">
        <h3 className="settings-section-title">About</h3>
        <div className="settings-about">
          <p className="text-sm"><strong>ParkSense AI</strong> — Smart Parking System v1.0</p>
          <p className="text-xs text-muted mt-2">Vehicle detection powered by YOLOv8. Backend: FastAPI + OpenCV. Frontend: React.</p>
          <p className="text-xs text-muted">Video input: MP4/AVI/MOV files, RTSP/HTTP streams, IP cameras, USB webcams.</p>
        </div>
      </div>

      <div className="flex gap-3 mt-4">
        <button className="btn btn-primary" onClick={save}>Save Settings</button>
        <button className="btn btn-ghost" onClick={() => setSettings({
          theme: 'dark', autoRefresh: true, refreshInterval: 2, notifications: true,
          detectionConf: 0.2, yoloEvery: 3, jpegQuality: 85
        })}>Reset Defaults</button>
      </div>
    </div>
  );
};

export default Settings;