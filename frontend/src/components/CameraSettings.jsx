import React, { useState, useEffect } from 'react';
import './CameraSettings.css';

export default function CameraSettings() {
  const [cameras, setCameras] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [testingCamera, setTestingCamera] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedCamera, setSelectedCamera] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    location: '',
    video_source: '',
    username: '',
    password: ''
  });

  useEffect(() => {
    loadCameras();
  }, []);

  const loadCameras = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8000/api/cameras');
      const data = await response.json();
      setCameras(data);
      setError(null);
    } catch (err) {
      setError('Failed to load cameras');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenForm = (camera = null) => {
    if (camera) {
      setIsEditing(true);
      setSelectedCamera(camera);
      setFormData({
        name: camera.name,
        location: camera.location,
        video_source: camera.video_source,
        username: camera.username || '',
        password: camera.password || ''
      });
    } else {
      setIsEditing(false);
      setSelectedCamera(null);
      setFormData({
        name: '',
        location: '',
        video_source: '',
        username: '',
        password: ''
      });
    }
    setShowForm(true);
  };

  const handleCloseForm = () => {
    setShowForm(false);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim() || !formData.video_source.trim()) {
      setError('Camera name and video source are required');
      return;
    }

    try {
      setError(null);

      const payload = {
        name: formData.name,
        location: formData.location,
        video_source: formData.video_source,
        username: formData.username || null,
        password: formData.password || null
      };

      if (isEditing) {
        const response = await fetch(
          `http://localhost:8000/api/cameras/${selectedCamera.id}`,
          {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          }
        );
        if (!response.ok) throw new Error('Failed to update camera');
      } else {
        const response = await fetch('http://localhost:8000/api/cameras', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error('Failed to add camera');
      }

      await loadCameras();
      handleCloseForm();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleTestCamera = async (camera) => {
    try {
      setTestingCamera(camera.id);
      setTestResult(null);
      
      const response = await fetch(
        `http://localhost:8000/api/cameras/${camera.id}/test`,
        { method: 'POST' }
      );

      const data = await response.json();
      
      if (!response.ok) {
        setTestResult({
          success: false,
          message: data.detail || 'Test failed'
        });
      } else {
        setTestResult({
          success: data.is_accessible,
          message: data.message
        });
      }
    } catch (err) {
      setTestResult({
        success: false,
        message: 'Error: ' + err.message
      });
    } finally {
      setTestingCamera(null);
    }
  };

  const handleDeleteCamera = async (camera) => {
    if (window.confirm(`Delete camera "${camera.name}"?`)) {
      try {
        const response = await fetch(
          `http://localhost:8000/api/cameras/${camera.id}`,
          { method: 'DELETE' }
        );
        if (!response.ok) throw new Error('Failed to delete camera');
        await loadCameras();
      } catch (err) {
        setError('Failed to delete camera: ' + err.message);
      }
    }
  };

  if (loading) {
    return <div className="camera-settings"><p>Loading cameras...</p></div>;
  }

  return (
    <div className="camera-settings">
      <div className="settings-header">
        <h2>🎥 Cameras</h2>
        <button className="btn-add" onClick={() => handleOpenForm()}>
          + Add Camera
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <div className="cameras-list">
        {cameras.length === 0 ? (
          <p className="no-cameras">No cameras yet. Click "+ Add Camera" to get started.</p>
        ) : (
          cameras.map(camera => (
            <div key={camera.id} className="camera-card">
              <div className="camera-info">
                <h3>{camera.name}</h3>
                <p>{camera.location}</p>
                <small>{camera.video_source}</small>
              </div>

              <div className="camera-actions">
                <button className="btn-test" onClick={() => handleTestCamera(camera)} disabled={testingCamera === camera.id}>
                  {testingCamera === camera.id ? 'Testing...' : 'Test'}
                </button>
                <button className="btn-edit" onClick={() => handleOpenForm(camera)}>Edit</button>
                <button className="btn-delete" onClick={() => handleDeleteCamera(camera)}>Delete</button>
              </div>

              {testResult && testingCamera === camera.id && (
                <div className={`test-result ${testResult.success ? 'success' : 'error'}`}>
                  {testResult.message}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={handleCloseForm}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{isEditing ? 'Edit Camera' : 'Add New Camera'}</h2>
              <button className="btn-close" onClick={handleCloseForm}>✕</button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Camera Name *</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="e.g., Main Gate Camera"
                  required
                />
              </div>

              <div className="form-group">
                <label>Location</label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleInputChange}
                  placeholder="e.g., Parking Lot A"
                />
              </div>

              <div className="form-group">
                <label>Video Source *</label>
                <input
                  type="text"
                  name="video_source"
                  value={formData.video_source}
                  onChange={handleInputChange}
                  placeholder="e.g., rtsp://192.168.1.100:554/stream or 0 for webcam"
                  required
                />
                <small>Webcam: 0 | File: video.mp4 | RTSP: rtsp://IP:554/stream | HTTP: http://IP:8080/stream</small>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Username (optional)</label>
                  <input
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    placeholder="admin"
                  />
                </div>

                <div className="form-group">
                  <label>Password (optional)</label>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    placeholder="••••••••"
                  />
                </div>
              </div>

              <div className="form-actions">
                <button type="submit" className="btn-submit">
                  {isEditing ? 'Update' : 'Add'} Camera
                </button>
                <button type="button" className="btn-cancel" onClick={handleCloseForm}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
