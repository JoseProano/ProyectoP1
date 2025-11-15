import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getPublicRooms, joinRoom } from '../services/api';
import './JoinRoom.css';

function JoinRoom() {
  const [rooms, setRooms] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [nickname, setNickname] = useState('');
  const [pin, setPin] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    loadRooms();
  }, []);

  const loadRooms = async () => {
    try {
      const data = await getPublicRooms();
      // El backend devuelve un array directamente, no {rooms: [...]}
      setRooms(Array.isArray(data) ? data : []);
    } catch (err) {
      setError('Error al cargar las salas disponibles');
    }
  };

  const handleRoomSelect = (room) => {
    setSelectedRoom(room);
    setError('');
    setPin('');
  };

  const handleJoinRoom = async (e) => {
    e.preventDefault();
    
    if (!nickname.trim()) {
      setError('Por favor ingresa un nickname');
      return;
    }

    if (!pin) {
      setError('Esta sala requiere un PIN');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Usar selectedRoom.id (no room_id)
      const response = await joinRoom(selectedRoom.id, nickname, pin || undefined);
      
      // Redirigir al chat con los parámetros de sesión
      navigate(`/chat?room_id=${encodeURIComponent(response.room_id)}&session_id=${encodeURIComponent(response.session_id)}&nickname=${encodeURIComponent(nickname)}`);
    } catch (err) {
      console.error('Error al unirse a la sala:', err);
      
      let errorMsg = 'Error al unirse a la sala';
      
      if (err.response?.data) {
        const data = err.response.data;
        
        // Intentar obtener mensaje estructurado
        if (data.error && typeof data.error === 'object') {
          errorMsg = data.error.message || errorMsg;
        } else if (data.detail) {
          errorMsg = typeof data.detail === 'string' ? data.detail : (data.detail.message || errorMsg);
        } else if (data.message) {
          errorMsg = data.message;
        }
      } else if (err.message) {
        errorMsg = err.message;
      }
      
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="join-room-container">
      <div className="join-room-card">
        <div className="header-with-back">
          <button onClick={() => navigate('/')} className="back-btn">
            ← Volver al inicio
          </button>
          <div className="header-title">
            <h1>💬 Chat Seguro ESPE</h1>
            <p className="subtitle">Selecciona una sala y únete a la conversación</p>
          </div>
        </div>

        {error && <div className="error-message">{error}</div>}

        {!selectedRoom ? (
          <div className="rooms-selection">
            <h2>Salas Disponibles</h2>
            <div className="rooms-list">
              {rooms.length === 0 ? (
                <p className="no-rooms">No hay salas disponibles en este momento</p>
              ) : (
                rooms.map(room => (
                  <div
                    key={room.id}
                    className="room-item"
                    onClick={() => handleRoomSelect(room)}
                  >
                    <div className="room-item-header">
                      <h3>{room.name}</h3>
                      <span className={`badge ${room.room_type}`}>{room.room_type}</span>
                    </div>
                    {room.description && (
                      <p className="room-item-description">{room.description}</p>
                    )}
                    <div className="room-item-footer">
                      <span>👥 {room.current_users}/{room.max_users}</span>
                      <span>🔒 PIN requerido</span>
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="admin-link">
              <button onClick={() => navigate('/admin')} className="btn btn-link">
                ¿Eres administrador? Ingresa aquí
              </button>
            </div>
          </div>
        ) : (
          <div className="join-form-container">
            <div className="selected-room-info">
              <h3>{selectedRoom.name}</h3>
              <p>{selectedRoom.description}</p>
              <button onClick={() => setSelectedRoom(null)} className="btn btn-link">
                ← Elegir otra sala
              </button>
            </div>

            <form onSubmit={handleJoinRoom} className="join-form">
              <div className="form-group">
                <label>Tu Nickname</label>
                <input
                  type="text"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  placeholder="Ej: Juan123"
                  required
                  maxLength="20"
                />
              </div>

              <div className="form-group">
                <label>PIN de la Sala 🔒</label>
                <input
                  type="password"
                  value={pin}
                  onChange={(e) => setPin(e.target.value)}
                  placeholder="Ingresa el PIN"
                  required
                  maxLength="8"
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-block"
                disabled={loading}
              >
                {loading ? 'Uniéndose...' : 'Unirse a la Sala'}
              </button>
            </form>
          </div>
        )}
      </div>

      <div className="footer-info">
        <p>Universidad de las Fuerzas Armadas ESPE</p>
        <p>Aplicaciones Distribuidas / Desarrollo de Software Seguro - Proyecto P1</p>
      </div>
    </div>
  );
}

export default JoinRoom;
