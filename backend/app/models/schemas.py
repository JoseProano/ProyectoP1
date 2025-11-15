"""
Modelos de datos Pydantic para validación y serializacion
"""
from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


class RoomType(str, Enum):
    """Tipos de sala"""
    TEXT = "text"
    MULTIMEDIA = "multimedia"


class UserRole(str, Enum):
    """Roles de usuario"""
    ADMIN = "admin"
    USER = "user"


# Modelos de Autenticación
class AdminLoginRequest(BaseModel):
    """Solicitud de login de administrador"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6)


class TokenResponse(BaseModel):
    """Respuesta con token JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TwoFactorSetupResponse(BaseModel):
    """Respuesta de configuración 2FA"""
    secret: str
    qr_code: str
    backup_codes: List[str]


# Modelos de Sala
class RoomCreateRequest(BaseModel):
    """Solicitud de creación de sala"""
    name: str = Field(..., min_length=3, max_length=100)
    room_type: RoomType
    pin: str = Field(..., min_length=4, max_length=8)
    description: Optional[str] = Field(None, max_length=500)
    max_users: int = Field(50, ge=2, le=100)
    
    @validator('pin')
    def validate_pin(cls, v):
        if not v.isdigit():
            raise ValueError('PIN must contain only digits')
        return v


class RoomResponse(BaseModel):
    """Respuesta con información de sala"""
    id: str
    name: str
    room_type: RoomType
    description: Optional[str]
    max_users: int
    current_users: int
    created_at: datetime
    created_by: str
    is_active: bool


class RoomJoinRequest(BaseModel):
    """Solicitud para unirse a una sala"""
    room_id: str
    pin: str = Field(..., min_length=4, max_length=8)
    nickname: str = Field(..., min_length=2, max_length=30)
    device_fingerprint: str = None  # Opcional, para pruebas de carga
    
    @validator('nickname')
    def validate_nickname(cls, v):
        # Prevenir XSS en nickname
        forbidden_chars = ['<', '>', '"', "'", '&', '/', '\\']
        if any(char in v for char in forbidden_chars):
            raise ValueError('Nickname contains forbidden characters')
        return v.strip()


# Modelos de Mensaje
class MessageSendRequest(BaseModel):
    """Solicitud de envío de mensaje"""
    room_id: str
    content: str = Field(..., min_length=1, max_length=5000)
    encrypted: bool = True
    
    @validator('content')
    def validate_content(cls, v):
        # Sanitizar contenido
        return v.strip()


class MessageResponse(BaseModel):
    """Respuesta con mensaje"""
    id: str
    room_id: str
    user_nickname: str
    content: str
    encrypted: bool
    timestamp: datetime
    signature: Optional[str]


# Modelos de Archivo
class FileMetadata(BaseModel):
    """Metadatos de archivo"""
    filename: str
    size: int
    content_type: str
    upload_timestamp: datetime
    uploader_nickname: str
    room_id: str
    file_hash: str
    is_verified: bool
    stego_detected: bool
    entropy_score: Optional[float]


class FileUploadResponse(BaseModel):
    """Respuesta de carga de archivo"""
    file_id: str
    filename: str
    url: str
    metadata: FileMetadata
    security_check: dict


# Modelos de Usuario en Sala
class RoomUser(BaseModel):
    """Usuario conectado en una sala"""
    nickname: str
    nickname_hash: str
    session_id: str
    joined_at: datetime
    ip_address: str
    last_activity: datetime


class RoomUsersResponse(BaseModel):
    """Lista de usuarios en sala"""
    room_id: str
    users: List[RoomUser]
    total_users: int


# Modelos de Logs y Auditoría
class AuditLog(BaseModel):
    """Log de auditoría"""
    id: str
    action: str
    user_id: str
    user_role: UserRole
    room_id: Optional[str]
    ip_address: str
    timestamp: datetime
    details: dict
    signature: str


class SecurityAlert(BaseModel):
    """Alerta de seguridad"""
    id: str
    alert_type: str
    severity: Literal["low", "medium", "high", "critical"]
    room_id: Optional[str]
    user_id: Optional[str]
    description: str
    timestamp: datetime
    resolved: bool


# Modelos de Sesión
class SessionInfo(BaseModel):
    """Información de sesión"""
    session_id: str
    user_id: str
    room_id: Optional[str]
    ip_address: str
    device_fingerprint: str
    created_at: datetime
    expires_at: datetime
    is_active: bool


# Modelos de Respuesta Genéricos
class SuccessResponse(BaseModel):
    """Respuesta exitosa genérica"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Respuesta de error"""
    success: bool = False
    error: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Modelos de WebSocket
class WebSocketMessage(BaseModel):
    """Mensaje WebSocket"""
    type: Literal["message", "join", "leave", "file", "system", "error"]
    room_id: str
    data: dict
    timestamp: datetime = Field(default_factory=datetime.utcnow)
