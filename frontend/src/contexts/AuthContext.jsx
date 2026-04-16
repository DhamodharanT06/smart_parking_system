import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Default admin credentials
const DEFAULT_ADMIN = {
  id: 1,
  username: 'admin',
  password: 'admin123', // In production, this should be hashed
  email: 'admin@smartparking.com',
  role: 'admin',
  name: 'Administrator',
  createdAt: new Date().toISOString()
};

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Initialize users in localStorage if not exists
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    if (users.length === 0) {
      localStorage.setItem('users', JSON.stringify([DEFAULT_ADMIN]));
    }

    // Check for existing session
    const session = JSON.parse(localStorage.getItem('currentUser') || 'null');
    if (session) {
      setCurrentUser(session);
    }
    setLoading(false);
  }, []);

  const login = (username, password) => {
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    const user = users.find(u => u.username === username && u.password === password);
    
    if (user) {
      const userSession = { ...user };
      delete userSession.password; // Don't store password in session
      setCurrentUser(userSession);
      localStorage.setItem('currentUser', JSON.stringify(userSession));
      return { success: true, user: userSession };
    }
    
    return { success: false, message: 'Invalid username or password' };
  };

  const signup = (userData) => {
    const users = JSON.parse(localStorage.getItem('users') || '[]');
    
    // Check if username already exists
    if (users.find(u => u.username === userData.username)) {
      return { success: false, message: 'Username already exists' };
    }

    // Check if email already exists
    if (users.find(u => u.email === userData.email)) {
      return { success: false, message: 'Email already exists' };
    }

    const newUser = {
      id: users.length + 1,
      ...userData,
      role: 'user', // Default role
      createdAt: new Date().toISOString()
    };

    users.push(newUser);
    localStorage.setItem('users', JSON.stringify(users));

    const userSession = { ...newUser };
    delete userSession.password;
    setCurrentUser(userSession);
    localStorage.setItem('currentUser', JSON.stringify(userSession));

    return { success: true, user: userSession };
  };

  const logout = () => {
    setCurrentUser(null);
    localStorage.removeItem('currentUser');
  };

  const updateProfile = (updates) => {
    if (!currentUser) return { success: false, message: 'No user logged in' };

    const users = JSON.parse(localStorage.getItem('users') || '[]');
    const userIndex = users.findIndex(u => u.id === currentUser.id);

    if (userIndex === -1) {
      return { success: false, message: 'User not found' };
    }

    users[userIndex] = { ...users[userIndex], ...updates };
    localStorage.setItem('users', JSON.stringify(users));

    const updatedSession = { ...users[userIndex] };
    delete updatedSession.password;
    setCurrentUser(updatedSession);
    localStorage.setItem('currentUser', JSON.stringify(updatedSession));

    return { success: true, user: updatedSession };
  };

  const isAdmin = () => currentUser?.role === 'admin';
  const isUser = () => currentUser?.role === 'user';

  return (
    <AuthContext.Provider 
      value={{ 
        currentUser, 
        loading, 
        login, 
        signup, 
        logout, 
        updateProfile,
        isAdmin,
        isUser
      }}
    >
      {!loading && children}
    </AuthContext.Provider>
  );
};
