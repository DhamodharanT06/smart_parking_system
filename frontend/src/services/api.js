// API service to communicate with FastAPI backend
// Dynamically determine API URL based on environment

const getAPIBaseUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  const host = window.location.hostname || 'localhost';
  const protocol = window.location.protocol === 'https:' ? 'https' : 'http';
  return `${protocol}://${host}:8000/api`;
};

let API_BASE_URL = getAPIBaseUrl();

export let isConnected = false;

const handleResponse = async (response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({
      detail: `HTTP Error ${response.status}: ${response.statusText}`
    }));
    const error = new Error(errorData.detail || 'An error occurred');
    error.status = response.status;
    error.data = errorData;
    throw error;
  }
  return response.json();
};

const fetchWithErrorHandling = async (url, options = {}) => {
  try {
    const response = await fetch(url, options);
    isConnected = true;
    return await handleResponse(response);
  } catch (error) {
    isConnected = false;
    if (error.status) {
      console.error(`API Error [${error.status}]:`, error.message);
    } else {
      console.error('Network Error:', error.message);
      error.status = 0;
      error.message = 'Unable to connect to server. Please check your backend is running.';
    }
    throw error;
  }
};

const api = {
  // ─── System ───────────────────────────────────────────────────────────────
  health: async () => {
    try {
      const response = await fetch(`${API_BASE_URL.replace('/api', '')}/health`);
      isConnected = response.ok;
      return response.ok;
    } catch {
      isConnected = false;
      return false;
    }
  },

  // ─── Cameras ──────────────────────────────────────────────────────────────
  cameras: {
    getAll: () => fetchWithErrorHandling(`${API_BASE_URL}/cameras/`),
    getById: (id) => fetchWithErrorHandling(`${API_BASE_URL}/cameras/${id}`),
    getNearby: (latitude, longitude, radius = 5) =>
      fetchWithErrorHandling(
        `${API_BASE_URL}/cameras/nearby?latitude=${latitude}&longitude=${longitude}&radius=${radius}`
      ),
    add: (data) =>
      fetchWithErrorHandling(`${API_BASE_URL}/cameras/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    update: (id, data) =>
      fetchWithErrorHandling(`${API_BASE_URL}/cameras/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      }),
    delete: (id) =>
      fetchWithErrorHandling(`${API_BASE_URL}/cameras/${id}`, { method: 'DELETE' }),
    test: (id) =>
      fetchWithErrorHandling(`${API_BASE_URL}/cameras/${id}/test`, { method: 'POST' }),
    getFavorites: () => fetchWithErrorHandling(`${API_BASE_URL}/cameras/favorites`),
    addFavorite: (id) =>
      fetchWithErrorHandling(`${API_BASE_URL}/cameras/${id}/favorite`, { method: 'POST' }),
    removeFavorite: (id) =>
      fetchWithErrorHandling(`${API_BASE_URL}/cameras/${id}/favorite`, { method: 'DELETE' }),
  },

  // ─── Parking ──────────────────────────────────────────────────────────────
  parking: {
    getStatus: (cameraId, options = {}) => {
      const params = new URLSearchParams();
      if (options.statusMode) params.set('status_mode', options.statusMode);
      const qs = params.toString();
      return fetchWithErrorHandling(`${API_BASE_URL}/parking/${cameraId}/status${qs ? `?${qs}` : ''}`);
    },
    getStatistics: (cameraId) =>
      fetchWithErrorHandling(`${API_BASE_URL}/parking/${cameraId}/statistics`),
    getStream: (cameraId, options = {}) => {
      const params = new URLSearchParams();
      if (options.overlaySlots === false) params.set('overlay_slots', 'false');
      const qs = params.toString();
      return `${API_BASE_URL}/parking/${cameraId}/stream${qs ? `?${qs}` : ''}`;
    },
    getFrame: (cameraId, options = {}) => {
      const params = new URLSearchParams();
      if (options.overlaySlots === false) params.set('overlay_slots', 'false');
      const qs = params.toString();
      return `${API_BASE_URL}/parking/${cameraId}/frame${qs ? `?${qs}` : ''}`;
    },
  },

  // ─── Video ────────────────────────────────────────────────────────────────
  video: {
    listTrails: () => fetchWithErrorHandling(`${API_BASE_URL}/video/trail/list`),
    getTrailUrl: (videoName) => `${API_BASE_URL}/video/trail/${videoName}`,
  },
};

export default api;
export { getAPIBaseUrl };
