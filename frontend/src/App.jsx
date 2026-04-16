import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';
import MainLayout from './components/Layout/MainLayout';
import ConnectionStatus from './components/ConnectionStatus';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Cameras from './pages/Cameras';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import api from './services/api';
import './App.css';

function App() {
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    // Check backend connection periodically
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

    // Check every 10 seconds
    const interval = setInterval(checkConnection, 10000);

    return () => clearInterval(interval);
  }, []);

  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <ConnectionStatus isConnected={isConnected} />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/" element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }>
              <Route index element={<Dashboard />} />
              <Route path="cameras" element={<Cameras />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="settings" element={<Settings />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
