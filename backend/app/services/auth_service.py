"""
Servicio de autenticación y autorización
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
from fastapi import HTTPException, status

from app.database import db
from app.config import settings
from app.utils.security import (
    password_manager,
    jwt_manager,
    two_factor_auth,
    session_manager
)
from app.utils.logging import audit_logger, LogAction
from app.models.schemas import AdminLoginRequest, TokenResponse


class AuthService:
    """Servicio de autenticación"""
    
    async def initialize_admin(self):
        """Crea el administrador por defecto si no existe"""
        admins_collection = db.get_collection("admins")
        
        existing_admin = await admins_collection.find_one(
            {"username": settings.ADMIN_USERNAME}
        )
        
        if not existing_admin:
            admin_data = {
                "username": settings.ADMIN_USERNAME,
                "email": settings.ADMIN_EMAIL,
                "password_hash": password_manager.hash_password(settings.ADMIN_PASSWORD),
                "role": "admin",
                "two_factor_enabled": False,
                "two_factor_secret": None,
                "backup_codes": [],
                "created_at": datetime.utcnow(),
                "last_login": None,
                "is_active": True
            }
            
            await admins_collection.insert_one(admin_data)
            print(f"✓ Default admin created: {settings.ADMIN_USERNAME}")
    
    async def authenticate_admin(
        self,
        login_data: AdminLoginRequest,
        ip_address: str
    ) -> TokenResponse:
        """Autentica un administrador"""
        admins_collection = db.get_collection("admins")
        
        # Buscar administrador
        admin = await admins_collection.find_one(
            {"username": login_data.username}
        )
        
        if not admin or not admin.get("is_active"):
            audit_logger.security_alert(
                alert_type="failed_login",
                severity="medium",
                description=f"Failed login attempt for user: {login_data.username}",
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verificar contraseña
        if not password_manager.verify_password(
            login_data.password,
            admin["password_hash"]
        ):
            audit_logger.security_alert(
                alert_type="invalid_password",
                severity="medium",
                description=f"Invalid password for user: {login_data.username}",
                ip_address=ip_address
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verificar 2FA si está habilitado
        if admin.get("two_factor_enabled"):
            if not login_data.totp_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA code required"
                )
            
            if not two_factor_auth.verify_totp(
                admin["two_factor_secret"],
                login_data.totp_code
            ):
                audit_logger.security_alert(
                    alert_type="invalid_2fa",
                    severity="high",
                    description=f"Invalid 2FA code for user: {login_data.username}",
                    ip_address=ip_address
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid 2FA code"
                )
        
        # Actualizar último login
        await admins_collection.update_one(
            {"_id": admin["_id"]},
            {"$set": {"last_login": datetime.utcnow()}}
        )
        
        # Crear tokens
        token_data = {
            "sub": str(admin["_id"]),
            "username": admin["username"],
            "role": admin["role"]
        }
        
        access_token = jwt_manager.create_access_token(token_data)
        refresh_token = jwt_manager.create_refresh_token(token_data)
        
        # Log de auditoría
        audit_logger.audit_log(
            action=LogAction.ADMIN_LOGIN,
            user_id=str(admin["_id"]),
            user_role="admin",
            ip_address=ip_address,
            details={"username": admin["username"]}
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    async def verify_admin_token(self, token: str) -> dict:
        """Verifica un token de administrador"""
        try:
            payload = jwt_manager.decode_token(token)
            
            if payload.get("role") != "admin":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            
            return payload
        
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    
    async def enable_two_factor(self, admin_id: str) -> dict:
        """Habilita 2FA para un administrador"""
        admins_collection = db.get_collection("admins")
        
        # Generar secreto
        secret = two_factor_auth.generate_secret()
        
        # Obtener admin
        admin = await admins_collection.find_one({"_id": admin_id})
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
        
        # Generar URI para QR
        qr_uri = two_factor_auth.get_totp_uri(secret, admin["username"])
        
        # Generar códigos de respaldo
        backup_codes = two_factor_auth.generate_backup_codes()
        
        # Actualizar admin
        await admins_collection.update_one(
            {"_id": admin_id},
            {
                "$set": {
                    "two_factor_secret": secret,
                    "backup_codes": backup_codes,
                    "two_factor_enabled": False  # Se activa después de verificar
                }
            }
        )
        
        return {
            "secret": secret,
            "qr_uri": qr_uri,
            "backup_codes": backup_codes
        }
    
    async def verify_and_enable_2fa(
        self,
        admin_id: str,
        totp_code: str
    ) -> bool:
        """Verifica código 2FA y habilita 2FA"""
        admins_collection = db.get_collection("admins")
        
        admin = await admins_collection.find_one({"_id": admin_id})
        if not admin or not admin.get("two_factor_secret"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not initialized"
            )
        
        # Verificar código
        if not two_factor_auth.verify_totp(
            admin["two_factor_secret"],
            totp_code
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code"
            )
        
        # Habilitar 2FA
        await admins_collection.update_one(
            {"_id": admin_id},
            {"$set": {"two_factor_enabled": True}}
        )
        
        # Log
        audit_logger.audit_log(
            action=LogAction.ADMIN_2FA_ENABLED,
            user_id=str(admin_id),
            user_role="admin",
            ip_address="",
            details={"username": admin["username"]}
        )
        
        return True


# Instancia global
auth_service = AuthService()
