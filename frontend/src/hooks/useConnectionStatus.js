import { useState, useEffect } from 'react';
import api from '../services/api';

export const useConnectionStatus = (interval = 5000) => {
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        const connected = await api.health();
        setIsConnected(connected);
      } catch (error) {
        setIsConnected(false);
      }
    };

    // Check immediately
    checkConnection();

    // Set up periodic checks
    const intervalId = setInterval(checkConnection, interval);

    return () => clearInterval(intervalId);
  }, [interval]);

  return isConnected;
};
