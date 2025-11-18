import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { getMessages, uploadFile, downloadFile } from '../services/api';
import { encryptMessage, decryptMessage, clearRoomKey } from '../services/crypto';
import socketService from '../services/socket';
import './ChatRoom.css';

function ChatRoom() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [users, setUsers] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [myNickname, setMyNickname] = useState('');
  const [fileStatus, setFileStatus] = useState({ uploading: false, error: '' });
  const [roomInfo, setRoomInfo] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const roomId = searchParams.get('room_id');
  const sessionId = searchParams.get('session_id');
  const nickname = searchParams.get('nickname');

  const loadMessageHistory = async (rId, sId) => {
    try {
      const data = await getMessages(rId, sId);
      if (data.messages && data.messages.length > 0) {
        const decryptedMessages = data.messages.map(msg => ({
          ...msg,
          content: msg.encrypted_content ? decryptMessage(msg.encrypted_content, rId) : msg.content,
          decrypted: true
        }));
        setMessages(decryptedMessages);
      }
    } catch (error) {
      console.error('Error al cargar historial:', error);
      
      // Si hay error de sesión inválida, redirigir al inicio
      if (error.response?.status === 401 || error.response?.data?.detail?.includes('session')) {
        alert('Tu sesión ha expirado. Por favor, únete a la sala nuevamente.');
        navigate('/');
        return;
      }
      
      addSystemMessage('Error al cargar historial de mensajes');
    }
  };

  useEffect(() => {
    if (!roomId || !sessionId || !nickname) {
      alert('Faltan parámetros de sesión');
      navigate('/');
      return;
    }

    setMyNickname(nickname);

    // Conectar socket y unirse a la sala
    socketService.connect();
    socketService.joinRoom(sessionId, roomId, nickname);

    // Cargar historial de mensajes
    loadMessageHistory(roomId, sessionId);

    // Configurar listeners de Socket.IO
    socketService.onMessage((data) => {
      handleNewMessage(data);
    });

    socketService.onUserJoined((data) => {
      addSystemMessage(`${data.nickname} se ha unido a la sala`);
      setUsers(data.users || []);
    });

    socketService.onUserLeft((data) => {
      addSystemMessage(`${data.nickname} ha abandonado la sala`);
      setUsers(data.users || []);
    });

    socketService.onUserList((data) => {
      setUsers(data.users || []);
    });

    socketService.onRoomInfo((data) => {
      setRoomInfo(data);
    });

    socketService.onError((data) => {
      const errorMessage = typeof data.message === 'string' 
        ? data.message 
        : 'Error de conexión con el servidor';
      addSystemMessage(`❌ Error: ${errorMessage}`);
    });

    // Manejar cierre de pestaña/navegador y recarga
    const handleBeforeUnload = (e) => {
      // Desconectar del chat en cualquier caso (cierre o recarga)
      socketService.leaveRoom(sessionId, roomId, nickname);
      socketService.disconnect();
    };

    window.addEventListener('beforeunload', handleBeforeUnload);

    // Cleanup al desmontar (cambio de ruta)
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      socketService.leaveRoom(sessionId, roomId, nickname);
      socketService.disconnect();
      // 🔐 Limpiar clave E2E al salir de la sala
      clearRoomKey(roomId);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roomId, sessionId, nickname, navigate]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleNewMessage = (data) => {
    // 🔐 E2E: Desencriptar mensaje con clave de la sala
    const decryptedContent = data.encrypted_content 
      ? decryptMessage(data.encrypted_content, roomId) 
      : data.content;
    
    setMessages(prev => [...prev, {
      ...data,
      content: decryptedContent,
      decrypted: true
    }]);
  };

  const addSystemMessage = (text) => {
    setMessages(prev => [...prev, {
      type: 'system',
      content: text,
      timestamp: new Date().toISOString()
    }]);
  };

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!inputMessage.trim()) return;

    // 🔐 E2E: Encriptar mensaje ANTES de enviarlo al servidor
    // El servidor NUNCA ve el contenido en texto plano
    const encrypted = encryptMessage(inputMessage, roomId);
    socketService.sendMessage({
      room_id: roomId,
      session_id: sessionId,
      nickname: myNickname,
      encrypted_content: encrypted,
      content: '[Encrypted]'  // El servidor solo ve esto
    });

    setInputMessage('');
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setFileStatus({ uploading: true, error: '' });

    try {
      const result = await uploadFile(roomId, file, sessionId);
      
      // Enviar mensaje de archivo compartido
      const fileMessage = `📎 Archivo compartido: ${result.filename}`;
      socketService.sendMessage({
        room_id: roomId,
        session_id: sessionId,
        nickname: myNickname,
        content: fileMessage,
        file_url: result.url,
        file_id: result.file_id,
        filename: result.filename
      });

      setFileStatus({ uploading: false, error: '' });
      fileInputRef.current.value = '';
    } catch (error) {
      console.error('Error al subir archivo:', error);
      let errorMsg = 'Error al subir archivo';
      
      // Intentar obtener el mensaje de error estructurado
      if (error.response?.data) {
        const data = error.response.data;
        
        // Caso 1: Error envuelto en {success, error, timestamp}
        if (data.error && typeof data.error === 'object') {
          errorMsg = data.error.message || errorMsg;
          if (data.error.details) {
            errorMsg += `\n${data.error.details}`;
          }
        }
        // Caso 2: Error directo en detail
        else if (data.detail) {
          const detail = data.detail;
          if (typeof detail === 'object') {
            errorMsg = detail.message || errorMsg;
            if (detail.details) {
              errorMsg += `\n${detail.details}`;
            }
          } else {
            errorMsg = detail;
          }
        }
      } else if (error.message) {
        errorMsg = error.message;
      }
      
      setFileStatus({ 
        uploading: false, 
        error: errorMsg
      });
    }
  };

  const handleLeaveRoom = () => {
    if (window.confirm('¿Estás seguro de que quieres abandonar la sala?')) {
      socketService.leaveRoom(sessionId, roomId, myNickname);
      socketService.disconnect();
      navigate('/');
    }
  };

  const handleDownloadFile = async (fileId, filename) => {
    try {
      await downloadFile(fileId, sessionId, filename);
      addSystemMessage(`✅ Archivo "${filename}" descargado correctamente`);
    } catch (error) {
      console.error('Error al descargar archivo:', error);
      let errorMsg = 'Error al descargar el archivo';
      
      if (error.response?.data) {
        const data = error.response.data;
        if (data.error && typeof data.error === 'object') {
          errorMsg = data.error.message || errorMsg;
        } else if (data.detail) {
          errorMsg = typeof data.detail === 'string' ? data.detail : data.detail.message || errorMsg;
        }
      }
      
      addSystemMessage(`❌ ${errorMsg}`);
    }
  };

  const formatTimestamp = (timestamp) => {
    // El timestamp viene del backend en formato ISO con zona horaria de Ecuador
    // Ejemplo: "2025-11-12T21:20:00-05:00"
    const date = new Date(timestamp);
    
    // Obtener la hora en Ecuador sin importar la zona horaria del navegador
    const formatter = new Intl.DateTimeFormat('es-EC', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false, // Formato 24 horas
      timeZone: 'America/Guayaquil'
    });
    
    return formatter.format(date);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="room-info-header">
          <button onClick={handleLeaveRoom} className="back-button">
            ← Volver
          </button>
          <div className="room-name-section">
            <div className="room-name-label">Sala:</div>
            <h2 className="room-name-title">{roomInfo?.room_name || 'Cargando...'}</h2>
            {roomInfo && (
              <span className={`room-type-badge ${roomInfo.room_type === 'multimedia' ? 'multimedia' : 'text'}`}>
                {roomInfo.room_type === 'multimedia' ? '📁 Multimedia' : '💬 Solo Texto'}
              </span>
            )}
          </div>
        </div>
        <div className="header-actions">
          <span className="user-badge">👤 {myNickname}</span>
          <button onClick={handleLeaveRoom} className="leave-button">
            Salir de la Sala
          </button>
        </div>
      </div>

      <div className="chat-layout">
        <div className="chat-main">
          <div className="messages-container">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.type || 'user'} ${msg.nickname === myNickname ? 'own' : ''}`}>
                {msg.type === 'system' ? (
                  <div className="system-message">{msg.content}</div>
                ) : (
                  <>
                    <div className="message-header">
                      <span className="message-nickname">{msg.nickname}</span>
                      <span className="message-time">{formatTimestamp(msg.timestamp)}</span>
                    </div>
                    <div className="message-content">
                      {msg.content}
                      {(msg.file_url || msg.file_id) && (
                        <div className="file-attachment">
                          <button 
                            onClick={() => {
                              const fileId = msg.file_id || msg.file_url.split('/').pop();
                              const filename = msg.filename || msg.content.split(': ')[1] || 'archivo';
                              handleDownloadFile(fileId, filename);
                            }}
                            className="download-button"
                          >
                            📥 Descargar archivo
                          </button>
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-container">
            {fileStatus.error && (
              <div className="file-error">{fileStatus.error}</div>
            )}
            
            <form onSubmit={handleSendMessage} className="message-form">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Escribe un mensaje..."
                disabled={fileStatus.uploading}
              />
              
              {/* Solo mostrar input de archivo y botón en salas multimedia */}
              {roomInfo?.room_type === 'multimedia' && (
                <>
                  <input
                    ref={fileInputRef}
                    type="file"
                    onChange={handleFileUpload}
                    style={{ display: 'none' }}
                  />
                  
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="btn btn-secondary"
                    disabled={fileStatus.uploading}
                  >
                    {fileStatus.uploading ? '⏳' : '📎'}
                  </button>
                </>
              )}
              
              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={!inputMessage.trim() || fileStatus.uploading}
              >
                Enviar
              </button>
            </form>
          </div>
        </div>

        <div className="chat-sidebar">
          <h3>Usuarios Conectados ({users.length})</h3>
          <ul className="users-list">
            {users.map((user, idx) => (
              <li key={idx} className={user.nickname === myNickname ? 'own-user' : ''}>
                {user.nickname === myNickname ? '👤 ' : '👥 '}
                {user.nickname}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default ChatRoom;
