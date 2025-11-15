"""
Servicio de gestión de salas de chat
"""
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from bson import ObjectId

from app.database import db
from app.config import settings
from app.utils.security import crypto_manager, session_manager
from app.utils.logging import audit_logger, LogAction
from app.models.schemas import (
    RoomCreateRequest,
    RoomResponse,
    RoomJoinRequest,
    RoomType
)
from app.services.session_service import session_store


class RoomService:
    """Servicio de gestión de salas"""
    
    async def create_room(
        self,
        room_data: RoomCreateRequest,
        admin_id: str,
        admin_username: str,
        ip_address: str
    ) -> RoomResponse:
        """Crea una nueva sala de chat"""
        rooms_collection = db.get_collection("rooms")
        
        # Generar ID único y encriptado
        room_id = crypto_manager.generate_room_id()
        
        # Hashear PIN
        pin_hash = crypto_manager.hash_pin(room_data.pin)
        
        # Crear documento de sala
        room_document = {
            "room_id": room_id,
            "name": room_data.name,
            "room_type": room_data.room_type.value,
            "description": room_data.description,
            "pin_hash": pin_hash,
            "max_users": room_data.max_users,
            "created_by": admin_id,
            "created_by_username": admin_username,
            "created_at": datetime.utcnow(),
            "is_active": True,
            "total_messages": 0,
            "total_files": 0
        }
        
        try:
            result = await rooms_collection.insert_one(room_document)
            
            # Log de auditoría
            audit_logger.audit_log(
                action=LogAction.ROOM_CREATED,
                user_id=admin_id,
                user_role="admin",
                room_id=room_id,
                ip_address=ip_address,
                details={
                    "room_name": room_data.name,
                    "room_type": room_data.room_type.value
                }
            )
            
            return RoomResponse(
                id=room_id,
                name=room_data.name,
                room_type=room_data.room_type,
                description=room_data.description,
                max_users=room_data.max_users,
                current_users=0,
                created_at=room_document["created_at"],
                created_by=admin_username,
                is_active=True
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating room: {str(e)}"
            )
    
    async def get_room(self, room_id: str) -> Optional[dict]:
        """Obtiene información de una sala"""
        rooms_collection = db.get_collection("rooms")
        room = await rooms_collection.find_one({"room_id": room_id})
        return room
    
    async def list_rooms(self, admin_id: str) -> List[RoomResponse]:
        """Lista todas las salas creadas por un administrador (solo activas)"""
        rooms_collection = db.get_collection("rooms")
        
        cursor = rooms_collection.find({"created_by": admin_id, "is_active": True})
        rooms = []
        
        async for room in cursor:
            # Obtener número actual de usuarios
            current_users = await session_store.get_room_user_count(room["room_id"])
            
            rooms.append(RoomResponse(
                id=room["room_id"],
                name=room["name"],
                room_type=RoomType(room["room_type"]),
                description=room.get("description"),
                max_users=room["max_users"],
                current_users=current_users,
                created_at=room["created_at"],
                created_by=room["created_by_username"],
                is_active=room["is_active"]
            ))
        
        return rooms
    
    async def list_all_active_rooms(self) -> List[RoomResponse]:
        """Lista todas las salas activas (público)"""
        rooms_collection = db.get_collection("rooms")
        
        cursor = rooms_collection.find({"is_active": True})
        rooms = []
        
        async for room in cursor:
            # Obtener número actual de usuarios
            current_users = await session_store.get_room_user_count(room["room_id"])
            
            rooms.append(RoomResponse(
                id=room["room_id"],
                name=room["name"],
                room_type=RoomType(room["room_type"]),
                description=room.get("description"),
                max_users=room["max_users"],
                current_users=current_users,
                created_at=room["created_at"],
                created_by=room["created_by_username"],
                is_active=room["is_active"]
            ))
        
        return rooms
    
    async def join_room(
        self,
        join_data: RoomJoinRequest,
        ip_address: str,
        device_fingerprint: str
    ) -> dict:
        """Permite a un usuario unirse a una sala"""
        rooms_collection = db.get_collection("rooms")
        
        # Verificar que la sala existe
        room = await rooms_collection.find_one({"room_id": join_data.room_id})
        
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La sala no existe. Verifica el ID de la sala."
            )
        
        if not room["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Esta sala ha sido desactivada por el administrador."
            )
        
        # Verificar PIN
        if not crypto_manager.verify_pin(join_data.pin, room["pin_hash"]):
            audit_logger.security_alert(
                alert_type="invalid_room_pin",
                severity="medium",
                description=f"Invalid PIN attempt for room: {join_data.room_id}",
                room_id=join_data.room_id,
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="PIN incorrecto. Verifica el código de acceso."
            )
        
        # Verificar que el dispositivo no esté en otra sala
        # Restricción: Solo una sala a la vez por IP (dispositivo/ordenador)
        existing_room = await session_store.check_device_in_use(device_fingerprint)
        if existing_room and existing_room != join_data.room_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tu dispositivo (IP) ya está conectado a otra sala. Solo puedes estar en una sala a la vez. Sal de la otra sala primero."
            )
        
        # Verificar capacidad
        current_users = await session_store.get_room_user_count(join_data.room_id)
        if current_users >= room["max_users"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"La sala está llena. Capacidad máxima: {room['max_users']} usuarios."
            )
        
        # Verificar nickname único en la sala
        room_users = await session_store.get_room_users(join_data.room_id)
        existing_user = next((u for u in room_users if u["nickname"] == join_data.nickname), None)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El nombre de usuario '{join_data.nickname}' ya está en uso en esta sala. Por favor, elige otro."
            )
        
        # Crear sesión
        session_id = session_manager.generate_session_id()
        user_id = session_manager.hash_nickname(join_data.nickname, join_data.room_id)
        
        await session_store.create_session(
            session_id=session_id,
            user_id=user_id,
            room_id=join_data.room_id,
            ip_address=ip_address,
            device_fingerprint=device_fingerprint
        )
        
        # Agregar usuario a la sala
        await session_store.add_user_to_room(
            join_data.room_id,
            user_id,
            join_data.nickname
        )
        
        # Registrar dispositivo
        await session_store.register_device(device_fingerprint, join_data.room_id)
        
        # Log de auditoría
        audit_logger.audit_log(
            action=LogAction.USER_JOINED,
            user_id=user_id,
            user_role="user",
            room_id=join_data.room_id,
            ip_address=ip_address,
            details={
                "nickname": join_data.nickname,
                "room_name": room["name"]
            }
        )
        
        return {
            "session_id": session_id,
            "user_id": user_id,
            "room_id": join_data.room_id,
            "room_name": room["name"],
            "room_type": room["room_type"],
            "nickname": join_data.nickname
        }
    
    async def leave_room(
        self,
        session_id: str,
        room_id: str,
        user_id: str,
        device_fingerprint: str,
        ip_address: str
    ):
        """Usuario sale de una sala"""
        # Remover de sesión de sala
        await session_store.remove_user_from_room(room_id, user_id)
        
        # Eliminar sesión
        await session_store.delete_session(session_id)
        
        # Liberar dispositivo
        await session_store.unregister_device(device_fingerprint)
        
        # Log
        audit_logger.audit_log(
            action=LogAction.USER_LEFT,
            user_id=user_id,
            user_role="user",
            room_id=room_id,
            ip_address=ip_address
        )
    
    async def delete_room(
        self,
        room_id: str,
        admin_id: str,
        ip_address: str
    ):
        """Elimina una sala (solo admin creador)"""
        rooms_collection = db.get_collection("rooms")
        
        room = await rooms_collection.find_one({"room_id": room_id})
        
        if not room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Room not found"
            )
        
        if room["created_by"] != admin_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only room creator can delete it"
            )
        
        # Marcar como inactiva
        await rooms_collection.update_one(
            {"room_id": room_id},
            {"$set": {"is_active": False}}
        )
        
        # Log
        audit_logger.audit_log(
            action=LogAction.ROOM_DELETED,
            user_id=admin_id,
            user_role="admin",
            room_id=room_id,
            ip_address=ip_address,
            details={"room_name": room["name"]}
        )
        
        return {"success": True, "message": "Room deleted"}


# Instancia global
room_service = RoomService()
