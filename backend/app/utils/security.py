"""
Utilidades de criptografía y seguridad
"""
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
import base64
import hashlib
import hmac
from typing import Tuple, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp
import secrets
import json

from app.config import settings


# Configuración de hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CryptoManager:
    """Gestor de operaciones criptográficas"""
    
    def __init__(self):
        self.key = self._derive_key(settings.AES_KEY.encode())
    
    def _derive_key(self, password: bytes, salt: bytes = None) -> bytes:
        """Deriva una clave AES-256 desde una contraseña"""
        if salt is None:
            salt = b'secure_chat_salt_v1'  # En producción, usar salt aleatorio
        return PBKDF2(password, salt, dkLen=32, count=100000)
    
    def encrypt_aes(self, data: str) -> str:
        """
        Encripta datos usando AES-256-GCM
        Retorna: base64(nonce + tag + ciphertext)
        """
        try:
            cipher = AES.new(self.key, AES.MODE_GCM)
            ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
            
            # Combinar nonce + tag + ciphertext
            encrypted = cipher.nonce + tag + ciphertext
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            raise ValueError(f"Encryption failed: {str(e)}")
    
    def decrypt_aes(self, encrypted_data: str) -> str:
        """
        Desencripta datos usando AES-256-GCM
        """
        try:
            encrypted = base64.b64decode(encrypted_data.encode('utf-8'))
            
            # Extraer nonce (16 bytes), tag (16 bytes) y ciphertext
            nonce = encrypted[:16]
            tag = encrypted[16:32]
            ciphertext = encrypted[32:]
            
            cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def generate_room_id(self) -> str:
        """Genera un ID único y URL-safe para una sala"""
        # Usar token_urlsafe directamente para evitar problemas con / en URLs
        return secrets.token_urlsafe(24)  # 32 caracteres URL-safe
    
    def hash_pin(self, pin: str) -> str:
        """Hashea un PIN usando bcrypt"""
        return pwd_context.hash(pin)
    
    def verify_pin(self, plain_pin: str, hashed_pin: str) -> bool:
        """Verifica un PIN contra su hash"""
        return pwd_context.verify(plain_pin, hashed_pin)
    
    def hash_sha256(self, data: str) -> str:
        """Genera hash SHA-256 de datos"""
        return hashlib.sha256(data.encode()).hexdigest()
    
    def sign_data(self, data: str) -> str:
        """Firma datos usando HMAC-SHA256"""
        return hmac.new(
            self.key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """Verifica firma HMAC"""
        expected = self.sign_data(data)
        return hmac.compare_digest(expected, signature)
    
    def hash_file(self, file_bytes: bytes) -> str:
        """Genera hash SHA-256 de un archivo"""
        return hashlib.sha256(file_bytes).hexdigest()


class JWTManager:
    """Gestor de tokens JWT"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Crea un token de acceso JWT"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Crea un token de refresco"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> dict:
        """Decodifica y valida un token JWT"""
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> bool:
        """Verifica si un token es válido"""
        try:
            payload = JWTManager.decode_token(token)
            return payload.get("type") == token_type
        except:
            return False


class TwoFactorAuth:
    """Gestor de autenticación de dos factores"""
    
    @staticmethod
    def generate_secret() -> str:
        """Genera un secreto TOTP"""
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp_uri(secret: str, username: str, issuer: str = "SecureChat") -> str:
        """Genera URI para código QR de TOTP"""
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=issuer)
    
    @staticmethod
    def verify_totp(secret: str, token: str) -> bool:
        """Verifica un código TOTP"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> list:
        """Genera códigos de respaldo"""
        return [secrets.token_hex(4).upper() for _ in range(count)]


class PasswordManager:
    """Gestor de contraseñas"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashea una contraseña"""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, str]:
        """
        Valida la fortaleza de una contraseña
        Requisitos: min 8 chars, mayúscula, minúscula, número, símbolo
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not any(c.isupper() for c in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(c.islower() for c in password):
            return False, "Password must contain at least one lowercase letter"
        
        if not any(c.isdigit() for c in password):
            return False, "Password must contain at least one digit"
        
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if not any(c in special_chars for c in password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"


class SessionManager:
    """Gestor de sesiones y fingerprinting"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Genera un ID de sesión único"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def create_device_fingerprint(user_agent: str, ip_address: str) -> str:
        """
        Crea una huella digital del dispositivo basada solo en IP.
        Esto asegura que un dispositivo (ordenador) solo pueda estar en una sala a la vez,
        independientemente del navegador usado.
        """
        # Solo usar IP para identificar el dispositivo (requisito: sesión única por IP)
        data = f"{ip_address}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def hash_nickname(nickname: str, room_id: str) -> str:
        """Hashea un nickname para privacidad"""
        data = f"{nickname}_{room_id}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# Instancias globales
crypto_manager = CryptoManager()
jwt_manager = JWTManager()
two_factor_auth = TwoFactorAuth()
password_manager = PasswordManager()
session_manager = SessionManager()
