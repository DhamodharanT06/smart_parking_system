import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '../../contexts/AuthContext';
import './Header.css';

const Header = ({ title, subtitle }) => {
  const { theme, changeTheme } = useTheme();
  const { currentUser, logout } = useAuth();

  const handleThemeChange = (e) => {
    changeTheme(e.target.value);
  };

  return (
    <header className="page-header">
      <div className="header-content">
        <div className="header-text">
          <h1 className="header-title">{title}</h1>
          {subtitle && <p className="header-subtitle">{subtitle}</p>}
        </div>
        <div className="header-actions">
          <div className="theme-selector">
            <select value={theme} onChange={handleThemeChange}>
              <option value="light">☀️ Light</option>
              <option value="dark">🌙 Dark</option>
              <option value="system">💻 System</option>
            </select>
          </div>
          <div className="user-info-header">
            <span className="user-name">{currentUser?.name || currentUser?.username}</span>
            <span className="user-role">{currentUser?.role}</span>
          </div>
          <button className="logout-btn" onClick={logout} title="Logout">
            🚪
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
