"""
Pruebas de carga con Locust para SecureChat
Prueba soporte de 50+ usuarios simultáneos por sala con hilos escalables
"""
from locust import HttpUser, task, between, events
import socketio
import json
import random
import string
from datetime import datetime


class SecureChatUser(HttpUser):
    """Usuario simulado de SecureChat"""
    
    wait_time = between(2, 5)  # Espera entre 2-5 segundos entre acciones
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.room_id = None
        self.nickname = None
        self.device_fingerprint = None
        self.sio = None
        self.connected = False
        self.joined_room = False  # Flag para evitar múltiples joins
    
    def on_start(self):
        """Se ejecuta cuando inicia cada usuario simulado"""
        # Generar datos únicos para este usuario
        self.nickname = f"User_{self.random_string(6)}"
        self.device_fingerprint = self.random_string(16)
        
        # Unirse a la sala una sola vez
        if not self.joined_room:
            self.join_room()
            
        # Conectar WebSocket una sola vez después de unirse
        if self.session_id and not self.connected:
            self.connect_websocket()
    
    def on_stop(self):
        """Se ejecuta cuando termina la simulación del usuario"""
        # Desconectar WebSocket - limpia la sesión automáticamente
        if self.sio and self.connected and self.session_id and self.room_id:
            try:
                # Emitir evento correcto de salida antes de desconectar (igual que frontend)
                self.sio.emit('leave_room_ws', {
                    'session_id': self.session_id,
                    'room_id': self.room_id,
                    'nickname': self.nickname
                })
                # Pausa para que el servidor procese el evento
                import time
                time.sleep(0.3)
                self.sio.disconnect()
                self.connected = False
            except Exception as e:
                pass
    
    @staticmethod
    def random_string(length=8):
        """Genera string aleatorio"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    def join_room(self):
        """Unirse a sala existente - SOLO UNA VEZ"""
        if self.joined_room:
            return
            
        # Room ID configurado automáticamente por auto_setup.py
        room_id = "REPLACE_WITH_REAL_ROOM_ID"
        pin = "1234"
        
        join_data = {
            "room_id": room_id,
            "pin": pin,
            "nickname": self.nickname,
            "device_fingerprint": self.device_fingerprint
        }
        
        with self.client.post(
            "/api/rooms/join",
            json=join_data,
            catch_response=True,
            name="/api/rooms/join"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                self.session_id = data.get("session_id")
                self.room_id = data.get("room_id", room_id)
                self.joined_room = True  # Marcar como unido
                response.success()
            elif response.status_code == 404:
                response.failure(f"Room not found")
            elif response.status_code == 401:
                response.failure(f"Invalid room PIN")
            elif response.status_code == 403:
                response.failure(f"Room is full")
            else:
                response.failure(f"Failed to join: {response.status_code}")
    
    def connect_websocket(self):
        """Conectar WebSocket para comunicación en tiempo real - SOLO UNA VEZ"""
        if self.connected or not self.session_id:
            return
        
        try:
            # Cliente Socket.IO
            self.sio = socketio.Client(
                reconnection=False,
                logger=False,
                engineio_logger=False
            )
            
            @self.sio.on('connect')
            def on_connect():
                self.connected = True
                # Unirse a la sala via WebSocket
                self.sio.emit('join_room', {
                    'session_id': self.session_id,
                    'room_id': self.room_id,
                    'nickname': self.nickname
                })
            
            @self.sio.on('new_message')
            def on_new_message(data):
                # Mensaje recibido exitosamente
                pass
            
            @self.sio.on('disconnect')
            def on_disconnect():
                self.connected = False
            
            @self.sio.on('error')
            def on_error(data):
                pass
            
            # Conectar al servidor
            host = self.host.replace('http://', '').replace('https://', '')
            self.sio.connect(
                f'http://{host}',
                transports=['websocket']
            )
            
        except Exception as e:
            pass
    
    @task(5)
    def send_message(self):
        """Enviar mensaje a la sala (tarea frecuente)"""
        if not self.sio or not self.connected:
            return
        
        message_content = f"Test message {self.random_string(10)} at {datetime.now().isoformat()}"
        
        try:
            self.sio.emit('send_message', {
                'session_id': self.session_id,
                'room_id': self.room_id,
                'nickname': self.nickname,
                'content': message_content
            })
            
            # Registrar evento para métricas de Locust
            events.request.fire(
                request_type="WebSocket",
                name="send_message",
                response_time=0,
                response_length=len(message_content),
                exception=None,
                context={}
            )
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="send_message",
                response_time=0,
                response_length=0,
                exception=e,
                context={}
            )
    
    @task(2)
    def get_room_messages(self):
        """Obtener mensajes históricos de la sala"""
        if not self.room_id or not self.session_id:
            return
        
        params = {"session_id": self.session_id, "limit": 50}
        
        with self.client.get(
            f"/api/messages/{self.room_id}",
            params=params,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get messages: {response.status_code}")
    
    @task(1)
    def check_session_activity(self):
        """Actualizar actividad de sesión"""
        if not self.sio or not self.connected:
            return
        
        try:
            self.sio.emit('update_activity', {
                'session_id': self.session_id
            })
            
            events.request.fire(
                request_type="WebSocket",
                name="update_activity",
                response_time=0,
                response_length=0,
                exception=None,
                context={}
            )
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="update_activity",
                response_time=0,
                response_length=0,
                exception=e,
                context={}
            )


class HeavyLoadUser(SecureChatUser):
    """Usuario con carga pesada - envía muchos mensajes"""
    wait_time = between(1, 3)  # Más rápido
    weight = 1  # 25% de usuarios
    
    @task(10)
    def send_message(self):
        """Enviar mensajes con más frecuencia"""
        super().send_message()


class LightLoadUser(SecureChatUser):
    """Usuario con carga ligera - mayormente observa"""
    wait_time = between(5, 10)  # Más lento
    weight = 3  # 75% de usuarios
    
    @task(2)
    def send_message(self):
        """Enviar mensajes ocasionalmente"""
        super().send_message()
    
    @task(5)
    def get_room_messages(self):
        """Leer mensajes más frecuentemente"""
        super().get_room_messages()
