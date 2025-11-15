import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getRooms, createRoom, deleteRoom } from '../services/api';
import './AdminDashboard.css';

function AdminDashboard() {
  const [rooms, setRooms] = useState([]);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    room_type: 'text',
    description: '',
    max_users: 10,
    pin: '1234'
  });

  const navigate = useNavigate();

  useEffect(() => {
    loadRooms();
  }, []);

  const loadRooms = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await getRooms();
      console.log('Respuesta de getRooms():', data);
      console.log('Tipo de data:', typeof data, Array.isArray(data));
      
      // Si data es un array directamente, usarlo; si no, buscar data.rooms
      const roomsList = Array.isArray(data) ? data : (data.rooms || []);
      console.log('Lista de salas a mostrar:', roomsList);
      setRooms(roomsList);
    } catch (err) {
      console.error('Error al cargar salas:', err);
      setError('Error al cargar salas: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'max_users' ? parseInt(value) : value
    }));
  };

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    setError('');
    
    // Validar PIN
    if (!formData.pin || formData.pin.length < 4 || formData.pin.length > 8) {
      setError('El PIN debe tener entre 4 y 8 dígitos');
      return;
    }
    
    if (!/^\d+$/.test(formData.pin)) {
      setError('El PIN debe contener solo números');
      return;
    }
    
    console.log('Creando sala con datos:', formData);
    
    try {
      const result = await createRoom(formData);
      console.log('Sala creada exitosamente:', result);
      setShowCreateForm(false);
      setFormData({
        name: '',
        room_type: 'text',
        description: '',
        max_users: 10,
        pin: '1234'
      });
      loadRooms();
    } catch (err) {
      console.error('Error al crear sala:', err);
      const errorMsg = err.response?.data?.detail || err.response?.data?.message || err.message || 'Error desconocido';
      setError('Error al crear sala: ' + errorMsg);
    }
  };

  const handleDeleteRoom = async (roomId) => {
    if (!window.confirm('¿Estás seguro de eliminar esta sala?')) return;
    
    try {
      await deleteRoom(roomId);
      loadRooms();
    } catch (err) {
      setError('Error al eliminar sala: ' + err.message);
    }
  };

  const handleOpenChat = (room) => {
    navigate(`/chat?room_id=${encodeURIComponent(room.id)}`);
  };

  const handleLogout = () => {
    localStorage.removeItem('adminToken');
    navigate('/admin');
  };

  if (loading) {
    return <div className="loading-container">Cargando salas...</div>;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <div className="header-left">
          <button onClick={() => navigate('/')} className="back-btn-dashboard">
            ← Inicio
          </button>
          <h1>Panel de Administración</h1>
        </div>
        <div className="header-actions">
          <button onClick={() => setShowCreateForm(true)} className="btn btn-primary">
            + Crear Nueva Sala
          </button>
          <button onClick={handleLogout} className="btn btn-secondary">
            Cerrar Sesión
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {showCreateForm && (
        <div className="modal-overlay" onClick={() => setShowCreateForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Crear Nueva Sala</h2>
            <form onSubmit={handleCreateRoom}>
              <div className="form-group">
                <label>Nombre de la Sala</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  required
                />
              </div>

              <div className="form-group">
                <label>Tipo de Sala</label>
                <select name="room_type" value={formData.room_type} onChange={handleInputChange}>
                  <option value="text">Texto</option>
                  <option value="multimedia">Multimedia</option>
                </select>
              </div>

              <div className="form-group">
                <label>Descripción</label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  rows="3"
                />
              </div>

              <div className="form-group">
                <label>Máximo de Usuarios</label>
                <input
                  type="number"
                  name="max_users"
                  value={formData.max_users}
                  onChange={handleInputChange}
                  min="2"
                  max="100"
                />
              </div>

              <div className="form-group">
                <label>PIN (4-8 dígitos, requerido)</label>
                <input
                  type="text"
                  name="pin"
                  value={formData.pin}
                  onChange={handleInputChange}
                  required
                  minLength="4"
                  maxLength="8"
                  pattern="[0-9]{4,8}"
                  placeholder="Ej: 1234"
                />
                <small>Solo números, mínimo 4 dígitos</small>
              </div>

              <div className="form-actions">
                <button type="submit" className="btn btn-primary">Crear Sala</button>
                <button type="button" onClick={() => setShowCreateForm(false)} className="btn btn-secondary">
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="rooms-grid">
        {rooms.length === 0 ? (
          <div className="no-rooms">
            <p>No hay salas creadas aún.</p>
            <p>Haz clic en "Crear Nueva Sala" para empezar.</p>
          </div>
        ) : (
          rooms.map(room => (
            <div key={room.id} className="room-card">
              <div className="room-header">
                <h3>{room.name}</h3>
                <span className={`room-type ${room.room_type}`}>{room.room_type}</span>
              </div>
              {room.description && (
                <p className="room-description">{room.description}</p>
              )}
              <div className="room-info">
                <span>👥 {room.current_users}/{room.max_users}</span>
                {room.pin && <span>🔒 Con PIN</span>}
              </div>
              <div className="room-id">
                <small>ID: {room.id}</small>
              </div>
              <div className="room-actions">
                <button onClick={() => handleOpenChat(room)} className="btn btn-sm btn-primary">
                  Abrir Chat
                </button>
                <button onClick={() => handleDeleteRoom(room.id)} className="btn btn-sm btn-danger">
                  Eliminar
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default AdminDashboard;
