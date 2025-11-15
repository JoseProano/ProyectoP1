"""
Aplicación principal FastAPI con WebSocket
"""
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List
import socketio
from datetime import datetime
import pytz
import json

from app.config import settings
from app.database import db
from app.services.session_service import session_store
from app.services.auth_service import auth_service
from app.services.room_service import room_service
from app.utils.security import crypto_manager, jwt_manager, session_manager
from app.utils.steganography_improved import improved_detector
from app.utils.logging import audit_logger, LogAction
from app.models.schemas import *

# Zona horaria de Ecuador
ECUADOR_TZ = pytz.timezone('America/Guayaquil')


def get_ecuador_time():
    """Retorna la hora actual en Ecuador"""
    return datetime.now(ECUADOR_TZ)


# Lifecycle
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida de la aplicación"""
    # Startup
    print("🚀 Starting Secure Chat Application...")
    
    # Conectar a bases de datos
    await db.connect_db()
    await session_store.connect()
    
    # Inicializar administrador por defecto
    await auth_service.initialize_admin()
    
    # Crear directorio de uploads
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    print("✓ Application started successfully")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await db.close_db()
    await session_store.close()
    print("✓ Application stopped")


# Crear aplicación FastAPI
app = FastAPI(
    title="Secure Chat API",
    description="Sistema de chat en tiempo real con salas seguras",
    version="1.0.0",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Seguridad HTTP Bearer
security = HTTPBearer()

# Socket.IO para WebSockets
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.cors_origins_list,
    logger=True,
    engineio_logger=False
)

# Montar Socket.IO
socket_app = socketio.ASGIApp(sio, app)

# Almacenamiento de conexiones WebSocket
websocket_connections: Dict[str, WebSocket] = {}


# ========== Dependencias ==========

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Verifica token de administrador"""
    try:
        token = credentials.credentials
        payload = await auth_service.verify_admin_token(token)
        return payload
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication"
        )


def get_client_ip(request: Request) -> str:
    """Obtiene IP del cliente"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host


async def check_rate_limit(request: Request):
    """Verifica rate limiting"""
    ip = get_client_ip(request)
    count = await session_store.increment_rate_limit(ip, window=60)
    
    if count > settings.RATE_LIMIT_PER_MINUTE:
        audit_logger.security_alert(
            alert_type="rate_limit_exceeded",
            severity="medium",
            description=f"Rate limit exceeded",
            ip_address=ip
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests"
        )


# ========== Rutas de Autenticación ==========

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(
    login_data: AdminLoginRequest,
    request: Request,
    _: None = Depends(check_rate_limit)
):
    """Login de administrador"""
    ip_address = get_client_ip(request)
    return await auth_service.authenticate_admin(login_data, ip_address)


@app.post("/api/auth/2fa/setup")
async def setup_2fa(
    admin: dict = Depends(get_current_admin)
):
    """Configura 2FA para administrador"""
    result = await auth_service.enable_two_factor(admin["sub"])
    return {"success": True, "data": result}


@app.post("/api/auth/2fa/verify")
async def verify_2fa(
    totp_code: str,
    admin: dict = Depends(get_current_admin)
):
    """Verifica y activa 2FA"""
    result = await auth_service.verify_and_enable_2fa(admin["sub"], totp_code)
    return {"success": True, "message": "2FA enabled successfully"}


# ========== Rutas de Salas ==========

@app.post("/api/rooms", response_model=RoomResponse)
async def create_room(
    room_data: RoomCreateRequest,
    request: Request,
    admin: dict = Depends(get_current_admin)
):
    """Crea una nueva sala de chat"""
    ip_address = get_client_ip(request)
    return await room_service.create_room(
        room_data,
        admin["sub"],
        admin["username"],
        ip_address
    )


@app.get("/api/rooms", response_model=List[RoomResponse])
async def list_rooms(
    admin: dict = Depends(get_current_admin)
):
    """Lista salas del administrador"""
    return await room_service.list_rooms(admin["sub"])


@app.get("/api/rooms/public", response_model=List[RoomResponse])
async def list_public_rooms():
    """Lista todas las salas activas (endpoint público)"""
    return await room_service.list_all_active_rooms()


@app.post("/api/rooms/join")
async def join_room(
    join_data: RoomJoinRequest,
    request: Request
):
    """Usuario se une a una sala"""
    ip_address = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")
    device_fingerprint = session_manager.create_device_fingerprint(user_agent, ip_address)
    
    return await room_service.join_room(join_data, ip_address, device_fingerprint)


@app.get("/api/messages/{room_id}")
async def get_room_messages(
    room_id: str,
    session_id: str,
    limit: int = 50
):
    """Obtiene el historial de mensajes de una sala"""
    print(f"[DEBUG] get_room_messages called - room_id: {room_id}, session_id: {session_id}")
    
    # Verificar sesión
    session = await session_store.get_session(session_id)
    if not session:
        print(f"[DEBUG] Session not found: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session - session not found"
        )
    
    if session.get("room_id") != room_id:
        print(f"[DEBUG] Room mismatch - session room: {session.get('room_id')}, requested: {room_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session - room mismatch"
        )
    
    # Obtener mensajes de la base de datos
    messages_collection = db.get_collection("messages")
    cursor = messages_collection.find({"room_id": room_id}).sort("timestamp", -1).limit(limit)
    messages = await cursor.to_list(length=limit)
    
    print(f"[DEBUG] Found {len(messages)} messages")
    
    # Desencriptar mensajes
    decrypted_messages = []
    for msg in reversed(messages):  # Invertir para que estén en orden cronológico
        try:
            decrypted_content = crypto_manager.decrypt_aes(msg["content"])
            
            # Usar nickname guardado en el mensaje, o buscar en room_users como fallback
            user_nick = msg.get("nickname", "Usuario")
            
            # Si no hay nickname en el mensaje (mensajes antiguos), buscar en Redis
            if user_nick == "Usuario":
                room_users = await session_store.get_room_users(room_id)
                for user in room_users:
                    if user.get("user_id") == msg["user_id"]:
                        user_nick = user.get("nickname", "Usuario")
                        break
            
            message_data = {
                "id": str(msg["_id"]),
                "nickname": user_nick,
                "content": decrypted_content,
                "timestamp": msg["timestamp"].astimezone(ECUADOR_TZ).isoformat()
            }
            
            # Incluir información de archivo si existe
            if msg.get("file_id"):
                message_data["file_id"] = msg["file_id"]
            if msg.get("filename"):
                message_data["filename"] = msg["filename"]
            if msg.get("file_url"):
                message_data["file_url"] = msg["file_url"]
            
            decrypted_messages.append(message_data)
        except Exception as e:
            print(f"Error decrypting message: {e}")
            continue
    
    print(f"[DEBUG] Returning {len(decrypted_messages)} decrypted messages")
    return {"messages": decrypted_messages}


@app.post("/api/rooms/{room_id}/upload")
async def upload_file(
    room_id: str,
    file: UploadFile = File(...),
    session_id: str = Form(None),
    request: Request = None
):
    """Sube un archivo a una sala multimedia"""
    print(f"[DEBUG] upload_file called - room_id: {room_id}, session_id from form: {session_id}")
    
    # Verificar sesión: aceptar session_id por Form, o por header X-Session-Id, o Authorization Bearer
    if not session_id and request:
        # Revisa header personalizado
        session_id = request.headers.get('X-Session-Id') or session_id
        # Revisa Authorization: Bearer <session>
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.lower().startswith('bearer '):
            session_id = session_id or auth_header.split(' ', 1)[1]
        
        print(f"[DEBUG] session_id from headers: {session_id}")

    session = None
    if session_id:
        session = await session_store.get_session(session_id)
        print(f"[DEBUG] Session retrieved: {session is not None}")

    if not session or session.get("room_id") != room_id:
        print(f"[DEBUG] Invalid session - session exists: {session is not None}, room match: {session.get('room_id') if session else 'N/A'} == {room_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session"
        )
    
    # Verificar tipo de sala
    room = await room_service.get_room(room_id)
    if not room or room["room_type"] != "multimedia":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Room does not support file uploads"
        )
    
    # Verificar tamaño
    file_bytes = await file.read()
    if len(file_bytes) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Max size: {settings.MAX_FILE_SIZE_MB}MB"
        )
    
    # Verificar tipo MIME
    # En producción usar python-magic
    content_type = file.content_type
    if content_type not in settings.allowed_file_types_list:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File type not allowed"
        )
    
    # Análisis de esteganografía mejorado
    if settings.ENABLE_STEGO_DETECTION:
        # Usar detector mejorado que distingue entre PDFs y imágenes
        analysis = improved_detector.analyze_file(
            file_bytes,
            file.filename,
            content_type
        )
        
        if analysis.get("is_suspicious"):
            # Registrar alerta
            audit_logger.security_alert(
                alert_type="steganography_detected",
                severity=analysis.get("threat_level", "medium"),
                description=f"Suspicious file detected: {file.filename}",
                user_id=session["user_id"],
                room_id=room_id,
                ip_address=get_client_ip(request),
                details=analysis
            )
            
            # Rechazar archivo
            audit_logger.audit_log(
                action=LogAction.FILE_REJECTED,
                user_id=session["user_id"],
                user_role="user",
                room_id=room_id,
                ip_address=get_client_ip(request),
                details={
                    "filename": file.filename,
                    "reason": "steganography_detected",
                    "analysis": analysis
                }
            )
            
            # Mensaje de error más detallado
            error_details = analysis.get('reason', 'Posible esteganografía detectada')
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "steganography_detected",
                    "message": f"Archivo rechazado: {error_details}",
                    "details": f"Tipo: {analysis.get('file_type', 'desconocido')}, Entropía: {analysis.get('file_entropy', 0):.2f}",
                    "threat_level": analysis.get("threat_level", "medium"),
                    "reason": error_details
                }
            )
    
    # Guardar archivo
    file_hash = crypto_manager.hash_file(file_bytes)
    # Generar ID único incluso para archivos duplicados
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    file_id = f"{room_id}_{file_hash[:16]}_{unique_id}"
    file_path = os.path.join(settings.UPLOAD_DIR, file_id)
    
    with open(file_path, "wb") as f:
        f.write(file_bytes)
    
    # Guardar metadata en DB
    files_collection = db.get_collection("files")
    file_metadata = {
        "file_id": file_id,
        "filename": file.filename,
        "room_id": room_id,
        "uploader_id": session["user_id"],
        "content_type": content_type,
        "size": len(file_bytes),
        "file_hash": file_hash,
        "upload_timestamp": get_ecuador_time(),
        "is_verified": True,
        "stego_analysis": analysis if settings.ENABLE_STEGO_DETECTION else None
    }
    
    await files_collection.insert_one(file_metadata)
    
    # Log
    audit_logger.audit_log(
        action=LogAction.FILE_UPLOADED,
        user_id=session["user_id"],
        user_role="user",
        room_id=room_id,
        ip_address=get_client_ip(request),
        details={
            "filename": file.filename,
            "size": len(file_bytes),
            "file_id": file_id
        }
    )
    
    # Notificar a la sala via WebSocket
    await sio.emit("file_uploaded", {
        "file_id": file_id,
        "filename": file.filename,
        "uploader": session.get("nickname", "Anonymous"),
        "size": len(file_bytes),
        "timestamp": get_ecuador_time().isoformat()
    }, room=room_id)
    
    return {
        "success": True,
        "file_id": file_id,
        "filename": file.filename,
        "url": f"/api/files/{file_id}",
        "verified": True
    }


@app.get("/api/files/{file_id}")
async def download_file(
    file_id: str,
    session_id: str
):
    """Descarga un archivo previamente subido"""
    from fastapi.responses import FileResponse
    import os
    
    print(f"Download request - file_id: {file_id}, session_id: {session_id}")
    
    # Verificar sesión
    session = await session_store.get_session(session_id)
    if not session:
        print(f"Session not found: {session_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión inválida o expirada"
        )
    
    print(f"Session found - room_id: {session.get('room_id')}, user_id: {session.get('user_id')}")
    
    # Buscar archivo en la base de datos
    files_collection = db.get_collection("files")
    file_doc = await files_collection.find_one({"file_id": file_id})
    
    if not file_doc:
        print(f"File not found in DB: {file_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Archivo no encontrado"
        )
    
    print(f"File found - room_id: {file_doc['room_id']}, uploader: {file_doc.get('uploader_id')}")
    
    # Verificar que el usuario esté en la misma sala que el archivo
    if file_doc["room_id"] != session.get("room_id"):
        print(f"Room mismatch - file room: {file_doc['room_id']}, session room: {session.get('room_id')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para descargar este archivo"
        )
    
    # Construir ruta del archivo
    file_path = os.path.join(settings.UPLOAD_DIR, file_id)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El archivo físico no existe en el servidor"
        )
    
    # Registrar descarga en audit log
    audit_logger.audit_log(
        action=LogAction.FILE_DOWNLOADED,
        user_id=session["user_id"],
        user_role="user",
        room_id=file_doc["room_id"],
        ip_address=session.get("ip_address", "unknown"),
        details={
            "file_id": file_id,
            "filename": file_doc["filename"]
        }
    )
    
    # Retornar archivo
    return FileResponse(
        path=file_path,
        filename=file_doc["filename"],
        media_type=file_doc.get("content_type", "application/octet-stream")
    )


@app.delete("/api/rooms/{room_id}")
async def delete_room(
    room_id: str,
    request: Request,
    admin: dict = Depends(get_current_admin)
):
    """Elimina una sala"""
    ip_address = get_client_ip(request)
    return await room_service.delete_room(room_id, admin["sub"], ip_address)


# ========== WebSocket Events ==========

@sio.event
async def connect(sid, environ):
    """Cliente WebSocket conectado"""
    print(f"WebSocket connected: {sid}")
    # Guardar mapeo de socket ID en el futuro si es necesario


@sio.event
async def disconnect(sid):
    """Cliente WebSocket desconectado - Limpiar sesiones automáticamente"""
    print(f"WebSocket disconnected: {sid}")
    
    try:
        # El cliente debe enviar leave_room_ws antes de desconectar
        # Si la desconexión es abrupta (cierre de pestaña), el evento beforeunload
        # del frontend debería manejar la limpieza
        # Socket.IO también enviará disconnect automáticamente
        pass
    except Exception as e:
        print(f"Error cleaning up disconnect: {e}")


@sio.event
async def join_room_ws(sid, data):
    """Usuario se une a sala via WebSocket"""
    try:
        session_id = data.get("session_id")
        room_id = data.get("room_id")
        
        # Verificar sesión
        session = await session_store.get_session(session_id)
        if not session or session["room_id"] != room_id:
            await sio.emit("error", {"message": "Invalid session"}, to=sid)
            return
        
        # Unir a sala Socket.IO
        await sio.enter_room(sid, room_id)
        
        # Obtener información de la sala
        room = await room_service.get_room(room_id)
        
        # Obtener lista actualizada de usuarios
        users = await session_store.get_room_users(room_id)
        
        # Notificar a otros usuarios que alguien se unió
        await sio.emit("user_joined", {
            "nickname": data.get("nickname"),
            "timestamp": get_ecuador_time().isoformat(),
            "users": users  # Incluir lista actualizada
        }, room=room_id, skip_sid=sid)
        
        # Enviar lista de usuarios al usuario que se acaba de unir
        await sio.emit("room_users", {"users": users}, to=sid)
        
        # Enviar información de la sala (incluyendo tipo)
        if room:
            await sio.emit("room_info", {
                "room_id": room_id,
                "room_name": room.get("name"),
                "room_type": room.get("room_type"),
                "description": room.get("description")
            }, to=sid)
        
    except Exception as e:
        await sio.emit("error", {"message": str(e)}, to=sid)


@sio.event
async def send_message(sid, data):
    """Enviar mensaje a sala"""
    try:
        session_id = data.get("session_id")
        room_id = data.get("room_id")
        content = data.get("content")
        
        # Verificar sesión
        session = await session_store.get_session(session_id)
        if not session or session["room_id"] != room_id:
            await sio.emit("error", {"message": "Invalid session"}, to=sid)
            return
        
        # Rate limiting para mensajes WebSocket
        rate_limit_key = f"ws_msg:{session_id}"
        count = await session_store.increment_rate_limit(rate_limit_key, window=60)
        
        if count > settings.RATE_LIMIT_MESSAGES_PER_MINUTE:
            audit_logger.security_alert(
                alert_type="rate_limit_exceeded",
                severity="medium",
                description=f"WebSocket message rate limit exceeded",
                user_id=session.get("user_id")
            )
            await sio.emit("error", {
                "message": f"Demasiados mensajes. Límite: {settings.RATE_LIMIT_MESSAGES_PER_MINUTE} mensajes/minuto"
            }, to=sid)
            return
        
        # Encriptar mensaje
        encrypted_content = crypto_manager.encrypt_aes(content)
        
        # Guardar en DB
        messages_collection = db.get_collection("messages")
        message_doc = {
            "room_id": room_id,
            "user_id": session["user_id"],
            "nickname": data.get("nickname", "Usuario"),  # Guardar nickname
            "content": encrypted_content,
            "encrypted": True,
            "timestamp": get_ecuador_time(),
            "signature": crypto_manager.sign_data(content)
        }
        
        # Guardar información de archivo si está presente
        if data.get("file_id"):
            message_doc["file_id"] = data.get("file_id")
        if data.get("filename"):
            message_doc["filename"] = data.get("filename")
        if data.get("file_url"):
            message_doc["file_url"] = data.get("file_url")
        
        result = await messages_collection.insert_one(message_doc)
        
        # Desencriptar para enviar (en producción, enviar encriptado)
        decrypted_content = content  # Ya viene desencriptado del cliente
        
        # Preparar mensaje para broadcast
        broadcast_message = {
            "id": str(result.inserted_id),
            "nickname": data.get("nickname"),
            "content": decrypted_content,
            "timestamp": message_doc["timestamp"].isoformat()
        }
        
        # Incluir información de archivo si está presente
        if data.get("file_id"):
            broadcast_message["file_id"] = data.get("file_id")
        if data.get("filename"):
            broadcast_message["filename"] = data.get("filename")
        if data.get("file_url"):
            broadcast_message["file_url"] = data.get("file_url")
        
        # Broadcast a la sala
        await sio.emit("new_message", broadcast_message, room=room_id)
        
        # Actualizar actividad
        await session_store.update_session_activity(session_id)
        
    except Exception as e:
        print(f"Error sending message: {e}")
        await sio.emit("error", {"message": "Error sending message"}, to=sid)


@sio.event
async def leave_room_ws(sid, data):
    """Usuario sale de sala"""
    try:
        session_id = data.get("session_id")
        room_id = data.get("room_id")
        
        session = await session_store.get_session(session_id)
        if session:
            # Limpiar primero
            await room_service.leave_room(
                session_id,
                room_id,
                session["user_id"],
                session["device_fingerprint"],
                session["ip_address"]
            )
            
            # Obtener lista actualizada de usuarios (después de eliminar)
            users = await session_store.get_room_users(room_id)
            
            # Notificar a la sala con lista actualizada
            await sio.emit("user_left", {
                "nickname": data.get("nickname"),
                "timestamp": get_ecuador_time().isoformat(),
                "users": users  # Incluir lista actualizada
            }, room=room_id, skip_sid=sid)
        
        await sio.leave_room(sid, room_id)
        
    except Exception as e:
        print(f"Error leaving room: {e}")


# ========== Rutas de Utilidad ==========

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "name": "Secure Chat API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "timestamp": get_ecuador_time().isoformat()
    }


@app.get("/api/logs/verify")
async def verify_logs(admin: dict = Depends(get_current_admin)):
    """Verifica integridad de logs"""
    return audit_logger.verify_log_integrity()


# Manejo de errores
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "timestamp": get_ecuador_time().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:socket_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        ssl_keyfile=settings.SSL_KEYFILE if settings.SSL_KEYFILE else None,
        ssl_certfile=settings.SSL_CERTFILE if settings.SSL_CERTFILE else None
    )
