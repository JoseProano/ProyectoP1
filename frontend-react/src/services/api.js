import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token de autenticación
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('admin_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Admin Auth
export const adminLogin = async (username, password) => {
  const response = await api.post('/auth/login', { username, password });
  if (response.data.access_token) {
    localStorage.setItem('admin_token', response.data.access_token);
  }
  return response.data;
};

export const adminLogout = () => {
  localStorage.removeItem('admin_token');
};

// Rooms
export const createRoom = async (roomData) => {
  const response = await api.post('/rooms', roomData);
  return response.data;
};

export const getRooms = async () => {
  const response = await api.get('/rooms');
  return response.data;
};

export const getPublicRooms = async () => {
  const response = await api.get('/rooms/public');
  return response.data;
};

export const deleteRoom = async (roomId) => {
  const response = await api.delete(`/rooms/${roomId}`);
  return response.data;
};

export const joinRoom = async (roomId, nickname, pin) => {
  const response = await api.post('/rooms/join', {
    room_id: roomId,
    nickname,
    pin,
  });
  return response.data;
};

// Messages
export const getMessages = async (roomId, sessionId, limit = 50) => {
  const response = await api.get(`/messages/${encodeURIComponent(roomId)}`, {
    params: { session_id: sessionId, limit },
  });
  return response.data;
};

export const getRoomMessages = async (roomId, sessionId, limit = 50) => {
  return getMessages(roomId, sessionId, limit);
};

// File Upload
export const uploadFile = async (roomId, file, sessionId) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);

  const response = await api.post(`/rooms/${encodeURIComponent(roomId)}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      'X-Session-Id': sessionId,
    },
  });
  return response.data;
};

// File Download
export const downloadFile = async (fileId, sessionId, filename) => {
  try {
    const response = await api.get(`/files/${fileId}`, {
      params: { session_id: sessionId },
      responseType: 'blob',
    });
    
    // Crear un link temporal para descargar
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
    
    return { success: true };
  } catch (error) {
    console.error('Error descargando archivo:', error);
    throw error;
  }
};

export default api;
