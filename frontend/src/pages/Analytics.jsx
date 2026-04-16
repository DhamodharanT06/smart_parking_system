import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api';
import './Analytics.css';


// ─── Mini gauge ────────────────────────────────────────────────
const Gauge = ({ pct, color }) => {
  const r = 40, c = 2 * Math.PI * r;
  const p = Math.min(100, Math.max(0, pct || 0));
  return (
    <svg width="100" height="100" viewBox="0 0 100 100">
      <circle cx="50" cy="50" r={r} fill="none" stroke="rgba(148,163,184,.15)" strokeWidth="10"/>
      <circle cx="50" cy="50" r={r} fill="none" stroke={color} strokeWidth="10"
        strokeDasharray={c} strokeDashoffset={c - (p / 100) * c}
        strokeLinecap="round" transform="rotate(-90 50 50)"
        style={{ transition: 'stroke-dashoffset .6s ease' }}/>
      <text x="50" y="54" textAnchor="middle" fill={color} fontSize="15" fontWeight="700">{Math.round(p)}%</text>
    </svg>
  );
};

const Analytics = () => {
  const [cameras, setCameras]     = useState([]);
  const [selected, setSelected]   = useState(null);
  const [stats, setStats]         = useState(null);
  const [history, setHistory]     = useState([]);
  const [loading, setLoading]     = useState(true);

  const loadCameras = useCallback(async () => {
    try {
      const data = await api.cameras.getAll();
      setCameras(data);
      if (data.length) setSelected(data[0]);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }, []);

  const loadStats = useCallback(async (camId) => {
    try {
      const s = await api.parking.getStatistics(camId);
      setStats(s);
      // append to history for the bar chart
      setHistory(h => [
        ...h.slice(-11),
        { label: new Date().toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}),
          occupied: s.occupied_slots, partial: s.partial_slots, free: s.available_slots }
      ]);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => { loadCameras(); }, [loadCameras]);

  useEffect(() => {
    if (!selected) return;
    loadStats(selected.id);
    const id = setInterval(() => loadStats(selected.id), 5000);
    return () => clearInterval(id);
  }, [selected, loadStats]);

  const total    = stats?.total_slots    || 0;
  const occupied = stats?.occupied_slots || 0;
  const partial  = stats?.partial_slots  || 0;
  const free     = stats?.available_slots|| 0;
  const oRate    = stats?.occupancy_rate || 0;

  const pieData = [
    { label: 'Free',     value: free,     color: 'var(--slot-free)' },
    { label: 'Partial',  value: partial,  color: 'var(--slot-partial)' },
    { label: 'Occupied', value: occupied, color: 'var(--slot-occupied)' },
  ];

  return (
    <div className="page-container">
      <div className="page-header flex justify-between items-center">
        <div><h1>Analytics</h1><p className="text-secondary">Occupancy trends and statistics per camera</p></div>
      </div>

      {/* Camera select */}
      <div className="card mb-4" style={{padding:'12px 16px'}}>
        <div className="flex items-center gap-3">
          <label className="text-sm text-secondary" style={{whiteSpace:'nowrap'}}>Camera:</label>
          <select
            style={{flex:1,maxWidth:360,background:'var(--bg-input)',color:'var(--text-primary)',border:'1px solid var(--border)',borderRadius:'var(--radius-sm)',padding:'7px 12px',fontSize:'.875rem'}}
            value={selected?.id||''}
            onChange={e=>setSelected(cameras.find(c=>c.id===e.target.value))}
          >
            {cameras.map(c=><option key={c.id} value={c.id}>{c.name} — {c.location}</option>)}
          </select>
        </div>
      </div>

      {stats ? (
        <>
          {/* KPI row */}
          <div className="grid-4 mb-4">
            <div className="card ana-kpi" style={{borderTopColor:'#818cf8'}}>
              <p className="text-sm text-secondary">Total Slots</p>
              <p className="ana-kpi-val" style={{color:'#818cf8'}}>{total}</p>
            </div>
            <div className="card ana-kpi" style={{borderTopColor:'var(--slot-free)'}}>
              <p className="text-sm text-secondary">Available</p>
              <p className="ana-kpi-val" style={{color:'var(--slot-free)'}}>{free}</p>
            </div>
            <div className="card ana-kpi" style={{borderTopColor:'var(--slot-partial)'}}>
              <p className="text-sm text-secondary">Partial</p>
              <p className="ana-kpi-val" style={{color:'var(--slot-partial)'}}>{partial}</p>
            </div>
            <div className="card ana-kpi" style={{borderTopColor:'var(--slot-occupied)'}}>
              <p className="text-sm text-secondary">Occupied</p>
              <p className="ana-kpi-val" style={{color:'var(--slot-occupied)'}}>{occupied}</p>
            </div>
          </div>

          {/* Gauge + pie legend + bar trend */}
          <div className="ana-main">
            {/* Occupancy gauge */}
            <div className="card">
              <h4 className="text-sm text-secondary mb-3">Occupancy Rate</h4>
              <div className="flex justify-between items-center">
                <Gauge pct={oRate} color={oRate<=40?'var(--slot-free)':oRate<=75?'var(--slot-partial)':'var(--slot-occupied)'}/>
                <div className="flex flex-col gap-3" style={{flex:1,marginLeft:16}}>
                  {pieData.map(d => (
                    <div key={d.label}>
                      <div className="flex justify-between text-sm mb-1">
                        <span style={{color:d.color}}>{d.label}</span>
                        <span className="font-bold" style={{color:d.color}}>{total?Math.round(d.value/total*100):0}%</span>
                      </div>
                      <div className="ana-progress-track">
                        <div className="ana-progress-bar" style={{width:`${total?d.value/total*100:0}%`,background:d.color}}/>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Live trend bar chart */}
            <div className="card">
              <h4 className="text-sm text-secondary mb-3">Live Trend (last 12 polls, 5s interval)</h4>
              <div className="ana-bar-wrap">
                {history.length === 0 ? (
                  <p className="text-sm text-muted">Collecting data…</p>
                ) : (
                  <div className="ana-stacked-chart">
                    {history.map((h, i) => (
                      <div key={i} className="ana-col">
                        <div className="ana-col-bars">
                          <div style={{flex:h.occupied,background:'var(--slot-occupied)',borderRadius:'3px 3px 0 0'}} title={`Occupied: ${h.occupied}`}/>
                          <div style={{flex:h.partial, background:'var(--slot-partial)'}} title={`Partial: ${h.partial}`}/>
                          <div style={{flex:h.free,    background:'var(--slot-free)', borderRadius:'0 0 3px 3px'}} title={`Free: ${h.free}`}/>
                        </div>
                        <span className="ana-col-label">{h.label}</span>
                      </div>
                    ))}
                  </div>
                )}
                {/* legend */}
                <div className="flex gap-3 mt-2">
                  {[['var(--slot-free)','Free'],['var(--slot-partial)','Partial'],['var(--slot-occupied)','Occupied']].map(([c,l])=>(
                    <span key={l} className="flex items-center gap-1 text-xs text-secondary">
                      <span style={{width:10,height:10,background:c,borderRadius:2,display:'inline-block'}}/>{l}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </>
      ) : loading ? (
        <div className="loading-center"><div className="spinner"/></div>
      ) : (
        <div className="dash-empty card"><div className="dash-empty-icon">📊</div><h2>No Data</h2><p className="text-secondary">Select a camera to view analytics.</p></div>
      )}
    </div>
  );
};

export default Analytics;