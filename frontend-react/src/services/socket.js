import { io } from 'socket.io-client';

const SOCKET_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class SocketService {
  constructor() {
    this.socket = null;
  }

  connect() {
    if (!this.socket) {
      this.socket = io(SOCKET_URL, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 5,
      });

      this.socket.on('connect', () => {
        console.log('✅ Socket conectado:', this.socket.id);
      });

      this.socket.on('disconnect', () => {
        console.log('❌ Socket desconectado');
      });

      this.socket.on('error', (error) => {
        console.error('Socket error:', error);
      });
    }
    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  joinRoom(sessionId, roomId, nickname) {
    if (this.socket) {
      this.socket.emit('join_room_ws', {
        session_id: sessionId,
        room_id: roomId,
        nickname,
      });
    }
  }

  leaveRoom(sessionId, roomId, nickname) {
    if (this.socket) {
      this.socket.emit('leave_room_ws', {
        session_id: sessionId,
        room_id: roomId,
        nickname,
      });
    }
  }

  sendMessage(data) {
    if (this.socket) {
      this.socket.emit('send_message', data);
    }
  }

  onMessage(callback) {
    if (this.socket) {
      this.socket.on('new_message', callback);
    }
  }

  onNewMessage(callback) {
    if (this.socket) {
      this.socket.on('new_message', callback);
    }
  }

  onUserJoined(callback) {
    if (this.socket) {
      this.socket.on('user_joined', callback);
    }
  }

  onUserLeft(callback) {
    if (this.socket) {
      this.socket.on('user_left', callback);
    }
  }

  onRoomUsers(callback) {
    if (this.socket) {
      this.socket.on('room_users', callback);
    }
  }

  onUserList(callback) {
    if (this.socket) {
      this.socket.on('room_users', callback);
    }
  }

  onRoomInfo(callback) {
    if (this.socket) {
      this.socket.on('room_info', callback);
    }
  }

  onFileUploaded(callback) {
    if (this.socket) {
      this.socket.on('file_uploaded', callback);
    }
  }

  onError(callback) {
    if (this.socket) {
      this.socket.on('error', callback);
    }
  }

  removeAllListeners() {
    if (this.socket) {
      this.socket.removeAllListeners();
    }
  }
}

const socketService = new SocketService();
export default socketService;
