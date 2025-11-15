"""
Sistema de logs auditables e inmutables con firmas digitales
"""
import json
import logging
import structlog
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path
import hashlib
from enum import Enum

from app.config import settings
from app.utils.security import crypto_manager


class LogAction(str, Enum):
    """Tipos de acciones auditables"""
    ADMIN_LOGIN = "admin_login"
    ADMIN_LOGOUT = "admin_logout"
    ADMIN_2FA_ENABLED = "admin_2fa_enabled"
    ROOM_CREATED = "room_created"
    ROOM_DELETED = "room_deleted"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    MESSAGE_SENT = "message_sent"
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_REJECTED = "file_rejected"
    STEGO_DETECTED = "steganography_detected"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SESSION_CREATED = "session_created"
    SESSION_TERMINATED = "session_terminated"
    SECURITY_ALERT = "security_alert"


class LogLevel(str, Enum):
    """Niveles de log"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """Sistema de logging auditable e inmutable"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Archivo de logs auditables (append-only)
        self.audit_log_file = self.log_dir / "audit.log"
        self.security_log_file = self.log_dir / "security.log"
        
        # Cadena de hashes para inmutabilidad (blockchain-like)
        self.chain_file = self.log_dir / "log_chain.json"
        self.chain = self._load_chain()
        
        # Configurar structlog
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        self.logger = structlog.get_logger()
    
    def _load_chain(self) -> List[dict]:
        """Carga la cadena de hashes de logs"""
        if self.chain_file.exists():
            try:
                with open(self.chain_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_chain(self):
        """Guarda la cadena de hashes"""
        with open(self.chain_file, 'w') as f:
            json.dump(self.chain, f, indent=2)
    
    def _get_previous_hash(self) -> str:
        """Obtiene el hash del último log en la cadena"""
        if len(self.chain) > 0:
            return self.chain[-1]['hash']
        return "0" * 64  # Hash génesis
    
    def _calculate_log_hash(self, log_entry: dict, previous_hash: str) -> str:
        """Calcula el hash de un log incluyendo el hash previo"""
        data = json.dumps(log_entry, sort_keys=True) + previous_hash
        return hashlib.sha256(data.encode()).hexdigest()
    
    def _sign_log(self, log_entry: dict) -> str:
        """Firma digitalmente un log"""
        data = json.dumps(log_entry, sort_keys=True)
        return crypto_manager.sign_data(data)
    
    def audit_log(
        self,
        action: LogAction,
        user_id: str,
        user_role: str,
        ip_address: str,
        room_id: Optional[str] = None,
        details: Optional[Dict] = None,
        level: LogLevel = LogLevel.INFO
    ) -> str:
        """
        Registra una acción auditable con firma digital
        Retorna el ID del log
        """
        timestamp = datetime.utcnow()
        log_id = hashlib.sha256(
            f"{action}_{user_id}_{timestamp.isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Crear entrada de log
        log_entry = {
            "id": log_id,
            "action": action.value,
            "user_id": user_id,
            "user_role": user_role,
            "room_id": room_id,
            "ip_address": ip_address,
            "timestamp": timestamp.isoformat(),
            "details": details or {},
            "level": level.value
        }
        
        # Firmar log
        signature = self._sign_log(log_entry)
        log_entry["signature"] = signature
        
        # Calcular hash con encadenamiento
        previous_hash = self._get_previous_hash()
        log_hash = self._calculate_log_hash(log_entry, previous_hash)
        
        # Agregar a la cadena
        chain_entry = {
            "log_id": log_id,
            "hash": log_hash,
            "previous_hash": previous_hash,
            "timestamp": timestamp.isoformat()
        }
        self.chain.append(chain_entry)
        self._save_chain()
        
        # Escribir al archivo (append-only)
        with open(self.audit_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Log estructurado
        self.logger.info(
            action.value,
            log_id=log_id,
            user_id=user_id,
            room_id=room_id,
            signature=signature[:16]
        )
        
        return log_id
    
    def security_alert(
        self,
        alert_type: str,
        severity: str,
        description: str,
        user_id: Optional[str] = None,
        room_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        """Registra una alerta de seguridad"""
        alert = {
            "id": hashlib.sha256(
                f"{alert_type}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()[:16],
            "alert_type": alert_type,
            "severity": severity,
            "description": description,
            "user_id": user_id,
            "room_id": room_id,
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {},
            "resolved": False
        }
        
        # Firmar alerta
        alert["signature"] = self._sign_log(alert)
        
        # Escribir a archivo de seguridad
        with open(self.security_log_file, 'a') as f:
            f.write(json.dumps(alert) + '\n')
        
        # Log crítico
        self.logger.critical(
            "security_alert",
            alert_type=alert_type,
            severity=severity,
            description=description
        )
        
        return alert["id"]
    
    def verify_log_integrity(self) -> Dict[str, any]:
        """
        Verifica la integridad de la cadena de logs
        Retorna resultado de la verificación
        """
        if len(self.chain) == 0:
            return {"valid": True, "message": "No logs to verify"}
        
        corrupted_logs = []
        
        for i, chain_entry in enumerate(self.chain):
            # Verificar que el hash previo coincida
            if i > 0:
                expected_prev = self.chain[i-1]['hash']
                if chain_entry['previous_hash'] != expected_prev:
                    corrupted_logs.append({
                        "log_id": chain_entry['log_id'],
                        "issue": "Previous hash mismatch"
                    })
        
        # Verificar firmas de logs
        try:
            with open(self.audit_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        log_entry = json.loads(line)
                        signature = log_entry.pop('signature')
                        
                        # Verificar firma
                        if not crypto_manager.verify_signature(
                            json.dumps(log_entry, sort_keys=True),
                            signature
                        ):
                            corrupted_logs.append({
                                "log_id": log_entry['id'],
                                "issue": "Invalid signature"
                            })
        except Exception as e:
            return {
                "valid": False,
                "message": f"Error verifying signatures: {str(e)}"
            }
        
        if len(corrupted_logs) > 0:
            return {
                "valid": False,
                "message": "Log integrity compromised",
                "corrupted_logs": corrupted_logs
            }
        
        return {
            "valid": True,
            "message": "All logs verified successfully",
            "total_logs": len(self.chain)
        }
    
    def get_logs(
        self,
        action: Optional[LogAction] = None,
        user_id: Optional[str] = None,
        room_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[dict]:
        """Recupera logs con filtros"""
        logs = []
        
        try:
            with open(self.audit_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        log = json.loads(line)
                        
                        # Aplicar filtros
                        if action and log.get('action') != action.value:
                            continue
                        if user_id and log.get('user_id') != user_id:
                            continue
                        if room_id and log.get('room_id') != room_id:
                            continue
                        
                        log_time = datetime.fromisoformat(log['timestamp'])
                        if start_date and log_time < start_date:
                            continue
                        if end_date and log_time > end_date:
                            continue
                        
                        logs.append(log)
                        
                        if len(logs) >= limit:
                            break
        except Exception as e:
            self.logger.error("error_reading_logs", error=str(e))
        
        return logs
    
    def get_security_alerts(
        self,
        severity: Optional[str] = None,
        resolved: Optional[bool] = None,
        limit: int = 100
    ) -> List[dict]:
        """Recupera alertas de seguridad"""
        alerts = []
        
        try:
            with open(self.security_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        alert = json.loads(line)
                        
                        if severity and alert.get('severity') != severity:
                            continue
                        if resolved is not None and alert.get('resolved') != resolved:
                            continue
                        
                        alerts.append(alert)
                        
                        if len(alerts) >= limit:
                            break
        except Exception as e:
            self.logger.error("error_reading_alerts", error=str(e))
        
        return alerts


# Instancia global
audit_logger = AuditLogger()
