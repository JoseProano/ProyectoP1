"""
Conexión y operaciones con MongoDB
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
import asyncio

from app.config import settings


class Database:
    """Gestor de conexión a MongoDB"""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect_db(cls):
        """Conecta a MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                serverSelectionTimeoutMS=5000
            )
            cls.db = cls.client[settings.DATABASE_NAME]
            
            # Verificar conexión
            await cls.client.admin.command('ping')
            print(f"✓ Connected to MongoDB: {settings.DATABASE_NAME}")
            
            # Crear índices
            await cls.create_indexes()
            
        except Exception as e:
            print(f"✗ Error connecting to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Cierra conexión a MongoDB"""
        if cls.client:
            cls.client.close()
            print("✓ MongoDB connection closed")
    
    @classmethod
    async def create_indexes(cls):
        """Crea índices para optimización"""
        try:
            # Índices para usuarios/administradores
            await cls.db.admins.create_index("username", unique=True)
            await cls.db.admins.create_index("email", unique=True)
            
            # Índices para salas
            await cls.db.rooms.create_index("room_id", unique=True)
            await cls.db.rooms.create_index("created_by")
            await cls.db.rooms.create_index("is_active")
            
            # Índices para mensajes
            await cls.db.messages.create_index([("room_id", 1), ("timestamp", -1)])
            await cls.db.messages.create_index("timestamp")
            
            # Índices para archivos
            await cls.db.files.create_index("room_id")
            await cls.db.files.create_index("file_hash", unique=True)
            
            # Índices para sesiones
            await cls.db.sessions.create_index("session_id", unique=True)
            await cls.db.sessions.create_index("expires_at")
            await cls.db.sessions.create_index([("room_id", 1), ("is_active", 1)])
            
            # Índices para logs (aunque usamos archivos, guardamos resumen en DB)
            await cls.db.audit_logs.create_index("timestamp")
            await cls.db.audit_logs.create_index("action")
            await cls.db.audit_logs.create_index("user_id")
            
            print("✓ Database indexes created")
            
        except Exception as e:
            print(f"✗ Error creating indexes: {e}")
    
    @classmethod
    def get_collection(cls, name: str):
        """Obtiene una colección de la base de datos"""
        if cls.db is None:
            raise RuntimeError("Database not connected")
        return cls.db[name]


# Instancia global
db = Database()


# Funciones helper
async def get_database() -> AsyncIOMotorDatabase:
    """Dependency para obtener la base de datos"""
    return db.db
