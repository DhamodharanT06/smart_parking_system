import React, { useEffect, useState } from 'react';
import { api } from '../services/api';
import './SlotGrid.css';

export default function SlotGrid({ slots: initialSlots, cameraId }) {
  const [slots, setSlots] = useState(initialSlots || []);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!cameraId) return;
    
    // Update slots when initialSlots change
    if (initialSlots && initialSlots.length > 0) {
      setSlots(initialSlots);
    } else {
      // Fetch if no initial slots provided
      fetchSlots();
    }
  }, [initialSlots, cameraId]);

  const fetchSlots = async () => {
    if (!cameraId) return;
    
    try {
      setLoading(true);
      const parkingStatus = await api.parking.getStatus(cameraId);
      if (parkingStatus && parkingStatus.slots) {
        setSlots(parkingStatus.slots);
      }
    } catch (err) {
      console.error('Failed to fetch slots:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="slot-grid-loading">⏳ Loading slots...</div>;
  }

  if (!slots || slots.length === 0) {
    return <div className="slot-grid-empty">No slots data available</div>;
  }

  return (
    <div className="slot-grid-container">
      <h3>Parking Slots ({slots.length})</h3>
      <div className="slot-grid">
        {slots.map(slot => (
          <div
            key={slot.id}
            className={`slot-item ${slot.status}`}
            title={`Slot ${slot.id}: ${slot.status}`}
          >
            <div className="slot-number">#{slot.id}</div>
            <div className="slot-status">{slot.status === 'available' ? '✓' : '✗'}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
