import React from 'react';
import './ConnectionStatus.css';

const ConnectionStatus = ({ isConnected }) => {
  if (isConnected) {
    return null;
  }

  return (
    <div className="connection-status-banner">
      <div className="connection-status-content">
        <span className="status-icon">⚠️</span>
        <span className="status-message">
          No connection to backend server. Some features may not work.
        </span>
      </div>
    </div>
  );
};

export default ConnectionStatus;
