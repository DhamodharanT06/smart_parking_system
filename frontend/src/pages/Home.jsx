import React, { useState, useCallback } from 'react';
import CameraSelector from '../components/CameraSelector';
import ParkingDashboard from '../components/ParkingDashboard';
import VideoStream from '../components/VideoStream';
import SlotGrid from '../components/SlotGrid';
import './Home.css';
import { api } from '../services/api';

export default function Home() {
  const [selectedCameraId, setSelectedCameraId] = useState(null);
  const [slots, setSlots] = useState([]);

  const handleCameraSelect = useCallback(async (cameraId) => {
    setSelectedCameraId(cameraId);
    setSlots([]); // Clear previous slots immediately
    try {
      const parkingStatus = await api.parking.getStatus(cameraId);
      if (parkingStatus && parkingStatus.slots) {
        setSlots(parkingStatus.slots);
      }
    } catch (err) {
      console.error('Failed to fetch parking status:', err);
      setSlots([]);
    }
  }, []);

  return (
    <div className="home">
      <div className="container">
        <header className="app-header">
          <h1>Smart Parking Management System</h1>
          <p>Real-time parking analytics powered by AI vision technology</p>
        </header>

        <div className="layout">
          <div className="sidebar">
            <CameraSelector 
              onCameraSelect={handleCameraSelect}
              selectedCameraId={selectedCameraId}
            />
          </div>

          <div className="main-content">
            {selectedCameraId ? (
              <>
                <VideoStream 
                  cameraId={selectedCameraId}
                  streamUrl={api.parking.getStream(selectedCameraId)}
                />
              </>
            ) : (
              <div className="welcome-message">
                <h2>🅿️ Smart Parking Management System</h2>
                <p>Select a camera from the left panel to monitor real-time parking availability and occupancy analytics</p>
              </div>
            )}
          </div>

          {selectedCameraId && (
            <div className="slot-details">
              <SlotGrid slots={slots} cameraId={selectedCameraId} />
            </div>
          )}
        </div>

        {selectedCameraId && (
          <div className="bottom-dashboard">
            <ParkingDashboard cameraId={selectedCameraId} />
          </div>
        )}
      </div>
    </div>
  );
}
