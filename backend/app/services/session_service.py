"""
Gestión de sesiones con Redis
"""
import json
from typing import Optional, Dict
from datetime import datetime, timedelta
import redis.asyncio as redis

from app.config import settings


class SessionStore:
    """Almacén de sesiones con Redis"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.session_prefix = "session:"
        self.room_users_prefix = "room:users:"
        self.user_device_prefix = "user:device:"
    
    async def connect(self):
        """Conecta a Redis"""
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            print("✓ Connected to Redis")
        except Exception as e:
            print(f"✗ Error connecting to Redis: {e}")
            # En modo desarrollo, continuar sin Redis
            self.redis = None
    
    async def close(self):
        """Cierra conexión a Redis"""
        if self.redis:
            await self.redis.close()
            print("✓ Redis connection closed")
    
    async def create_session(
        self,
        session_id: str,
        user_id: str,
        room_id: Optional[str],
        ip_address: str,
        device_fingerprint: str,
        expires_in: int = 3600
    ) -> bool:
        """Crea una nueva sesión"""
        if not self.redis:
            return True  # Modo sin Redis
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "room_id": room_id,
            "ip_address": ip_address,
            "device_fingerprint": device_fingerprint,
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
        key = f"{self.session_prefix}{session_id}"
        
        try:
            await self.redis.setex(
                key,
                expires_in,
                json.dumps(session_data)
            )
            return True
        except Exception as e:
            print(f"Error creating session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Obtiene datos de una sesión"""
        if not self.redis:
            return None
        
        try:
            key = f"{self.session_prefix}{session_id}"
            data = await self.redis.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
    
    async def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión"""
        if not self.redis:
            return True
        
        try:
            key = f"{self.session_prefix}{session_id}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    async def update_session_activity(self, session_id: str) -> bool:
        """Actualiza la actividad de una sesión"""
        if not self.redis:
            return True
        
        session = await self.get_session(session_id)
        if session:
            session["last_activity"] = datetime.utcnow().isoformat()
            key = f"{self.session_prefix}{session_id}"
            
            try:
                # Renovar TTL
                await self.redis.setex(
                    key,
                    3600,
                    json.dumps(session)
                )
                return True
            except Exception as e:
                print(f"Error updating session: {e}")
                return False
        
        return False
    
    async def add_user_to_room(self, room_id: str, user_id: str, nickname: str):
        """Agrega un usuario a una sala"""
        if not self.redis:
            return True
        
        try:
            key = f"{self.room_users_prefix}{room_id}"
            user_data = {
                "user_id": user_id,
                "nickname": nickname,
                "joined_at": datetime.utcnow().isoformat()
            }
            await self.redis.hset(key, user_id, json.dumps(user_data))
            return True
        except Exception as e:
            print(f"Error adding user to room: {e}")
            return False
    
    async def remove_user_from_room(self, room_id: str, user_id: str):
        """Remueve un usuario de una sala"""
        if not self.redis:
            return True
        
        try:
            key = f"{self.room_users_prefix}{room_id}"
            await self.redis.hdel(key, user_id)
            return True
        except Exception as e:
            print(f"Error removing user from room: {e}")
            return False
    
    async def get_room_users(self, room_id: str) -> list:
        """Obtiene lista de usuarios en una sala"""
        if not self.redis:
            return []
        
        try:
            key = f"{self.room_users_prefix}{room_id}"
            users_data = await self.redis.hgetall(key)
            
            users = []
            for user_json in users_data.values():
                users.append(json.loads(user_json))
            
            return users
        except Exception as e:
            print(f"Error getting room users: {e}")
            return []
    
    async def get_room_user_count(self, room_id: str) -> int:
        """Obtiene el número de usuarios en una sala"""
        if not self.redis:
            return 0
        
        try:
            key = f"{self.room_users_prefix}{room_id}"
            return await self.redis.hlen(key)
        except Exception as e:
            print(f"Error getting user count: {e}")
            return 0
    
    async def check_device_in_use(self, device_fingerprint: str) -> Optional[str]:
        """
        Verifica si un dispositivo ya está en uso
        Retorna el room_id si está en uso, None si no
        """
        if not self.redis:
            return None
        
        try:
            key = f"{self.user_device_prefix}{device_fingerprint}"
            room_id = await self.redis.get(key)
            return room_id
        except Exception as e:
            print(f"Error checking device: {e}")
            return None
    
    async def register_device(self, device_fingerprint: str, room_id: str):
        """Registra un dispositivo en uso para una sala"""
        if not self.redis:
            return True
        
        try:
            key = f"{self.user_device_prefix}{device_fingerprint}"
            # Expira en 1 hora
            await self.redis.setex(key, 3600, room_id)
            return True
        except Exception as e:
            print(f"Error registering device: {e}")
            return False
    
    async def unregister_device(self, device_fingerprint: str):
        """Libera un dispositivo"""
        if not self.redis:
            return True
        
        try:
            key = f"{self.user_device_prefix}{device_fingerprint}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            print(f"Error unregistering device: {e}")
            return False
    
    async def increment_rate_limit(self, key: str, window: int = 60) -> int:
        """
        Incrementa contador para rate limiting
        Retorna el número actual de requests
        """
        if not self.redis:
            return 0
        
        try:
            rate_key = f"rate:{key}"
            count = await self.redis.incr(rate_key)
            
            if count == 1:
                await self.redis.expire(rate_key, window)
            
            return count
        except Exception as e:
            print(f"Error incrementing rate limit: {e}")
            return 0
    
    async def cleanup_device_sessions(self, device_fingerprint: str) -> bool:
        """Limpia todas las sesiones de un dispositivo"""
        if not self.redis:
            return True
        
        try:
            # Desregistrar dispositivo
            await self.unregister_device(device_fingerprint)
            
            # Buscar todas las sesiones con este device_fingerprint
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor, 
                    match=f"{self.session_prefix}*",
                    count=100
                )
                
                for key in keys:
                    session_data = await self.redis.get(key)
                    if session_data:
                        data = json.loads(session_data)
                        if data.get("device_fingerprint") == device_fingerprint:
                            # Eliminar sesión
                            await self.redis.delete(key)
                            # Eliminar usuario de la sala
                            if data.get("room_id"):
                                await self.remove_user_from_room(
                                    data["room_id"],
                                    data["user_id"]
                                )
                
                if cursor == 0:
                    break
            
            return True
        except Exception as e:
            print(f"Error cleaning device sessions: {e}")
            return False
    
    async def cleanup_user_sessions(self, user_id: str) -> bool:
        """Limpia todas las sesiones de un usuario"""
        if not self.redis:
            return True
        
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor,
                    match=f"{self.session_prefix}*",
                    count=100
                )
                
                for key in keys:
                    session_data = await self.redis.get(key)
                    if session_data:
                        data = json.loads(session_data)
                        if data.get("user_id") == user_id:
                            # Eliminar sesión
                            await self.redis.delete(key)
                            # Desregistrar dispositivo si existe
                            if data.get("device_fingerprint"):
                                await self.unregister_device(data["device_fingerprint"])
                
                if cursor == 0:
                    break
            
            return True
        except Exception as e:
            print(f"Error cleaning user sessions: {e}")
            return False


# Instancia global
session_store = SessionStore()
