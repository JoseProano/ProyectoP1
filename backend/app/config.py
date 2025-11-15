"""
Configuración de la aplicación con variables de entorno
"""
from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Servidor
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Base de datos
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "secure_chat_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Encriptación
    AES_KEY: str = secrets.token_urlsafe(32)
    ENCRYPTION_KEY: str = secrets.token_urlsafe(32)
    
    # Administrador
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "Admin123!@#"
    ADMIN_EMAIL: str = "admin@securechat.local"
    
    # Archivos
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_TYPES: str = "image/jpeg,image/png,image/gif,application/pdf,text/plain"
    UPLOAD_DIR: str = "./uploads"
    
    # Esteganografía
    ENTROPY_THRESHOLD: float = 7.9
    ENABLE_STEGO_DETECTION: bool = True
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 30  # HTTP endpoints
    RATE_LIMIT_MESSAGES_PER_MINUTE: int = 30  # WebSocket messages
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Logs
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # SSL
    SSL_KEYFILE: str = ""
    SSL_CERTFILE: str = ""
    
    @property
    def allowed_file_types_list(self) -> List[str]:
        return self.ALLOWED_FILE_TYPES.split(',')
    
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',')]
    
    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
