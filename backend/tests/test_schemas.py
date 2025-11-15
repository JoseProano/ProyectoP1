"""
Tests para schemas.py (modelos Pydantic)
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import (
    AdminLoginRequest,
    RoomCreateRequest,
    RoomJoinRequest,
    MessageSendRequest,
    RoomResponse,
    MessageResponse,
    RoomType,
    TwoFactorSetupResponse
)


class TestAdminLoginRequest:
    """Tests para AdminLoginRequest"""
    
    def test_valid_admin_login(self):
        """Test login válido"""
        data = {
            "username": "admin",
            "password": "Admin123!@#"
        }
        request = AdminLoginRequest(**data)
        assert request.username == "admin"
        assert request.password == "Admin123!@#"
    
    def test_admin_login_with_totp(self):
        """Test login con código TOTP"""
        data = {
            "username": "admin",
            "password": "Admin123!@#",
            "totp_code": "123456"
        }
        request = AdminLoginRequest(**data)
        assert request.totp_code == "123456"
    
    def test_invalid_username(self):
        """Test username inválido"""
        with pytest.raises(ValidationError):
            AdminLoginRequest(username="ab", password="Pass123!@#")


class TestRoomCreateRequest:
    """Tests para RoomCreateRequest"""
    
    def test_create_text_room(self):
        """Test crear sala de texto"""
        data = {
            "name": "Sala de Prueba",
            "pin": "1234",
            "room_type": "text",
            "max_users": 10
        }
        room = RoomCreateRequest(**data)
        assert room.name == "Sala de Prueba"
        assert room.room_type == RoomType.TEXT
    
    def test_create_multimedia_room(self):
        """Test crear sala multimedia"""
        data = {
            "name": "Sala Multimedia",
            "pin": "5678",
            "room_type": "multimedia",
            "max_users": 20,
            "description": "Sala para compartir archivos"
        }
        room = RoomCreateRequest(**data)
        assert room.room_type == RoomType.MULTIMEDIA
        assert room.description == "Sala para compartir archivos"
    
    def test_invalid_pin_length(self):
        """Test PIN muy corto"""
        with pytest.raises(ValidationError):
            RoomCreateRequest(
                name="Test",
                pin="123",  # Muy corto
                room_type="text"
            )
    
    def test_invalid_room_type(self):
        """Test tipo de sala inválido"""
        with pytest.raises(ValidationError):
            RoomCreateRequest(
                name="Test",
                pin="1234",
                room_type="invalid"
            )
    
    def test_max_users_validation(self):
        """Test validación de usuarios máximos"""
        data = {
            "name": "Test",
            "pin": "1234",
            "room_type": "text",
            "max_users": 5
        }
        room = RoomCreateRequest(**data)
        assert room.max_users == 5


class TestRoomJoinRequest:
    """Tests para RoomJoinRequest"""
    
    def test_valid_join_request(self):
        """Test solicitud válida de unirse"""
        data = {
            "room_id": "abc123xyz",
            "nickname": "Usuario1",
            "pin": "1234"
        }
        request = RoomJoinRequest(**data)
        assert request.nickname == "Usuario1"
        assert request.pin == "1234"
    
    def test_nickname_validation_success(self):
        """Test nickname válido"""
        request = RoomJoinRequest(
            room_id="abc123",
            nickname="User",
            pin="1234"
        )
        assert request.nickname == "User"
    
    def test_nickname_too_long(self):
        """Test nickname muy largo"""
        with pytest.raises(ValidationError):
            RoomJoinRequest(
                room_id="abc123",
                nickname="a" * 51,  # Muy largo
                pin="1234"
            )


class TestMessageSendRequest:
    """Tests para MessageSendRequest"""
    
    def test_create_message(self):
        """Test crear mensaje"""
        data = {
            "content": "Hola mundo",
            "room_id": "room123"
        }
        message = MessageSendRequest(**data)
        assert message.content == "Hola mundo"
        assert message.room_id == "room123"
    
    def test_empty_message(self):
        """Test mensaje vacío"""
        with pytest.raises(ValidationError):
            MessageSendRequest(
                content="",
                room_id="room123"
            )


class TestRoomResponse:
    """Tests para RoomResponse"""
    
    def test_room_response(self):
        """Test respuesta de sala"""
        data = {
            "id": "room123",
            "name": "Mi Sala",
            "description": "Test room",
            "room_type": "multimedia",
            "max_users": 10,
            "current_users": 5,
            "is_active": True,
            "created_at": datetime.now(),
            "created_by": "admin1"
        }
        response = RoomResponse(**data)
        assert response.id == "room123"
        assert response.current_users == 5


class TestMessageResponse:
    """Tests para MessageResponse"""
    
    def test_message_response(self):
        """Test respuesta de mensaje"""
        data = {
            "id": "msg123",
            "content": "Test message",
            "user_nickname": "User1",
            "room_id": "room123",
            "timestamp": datetime.now(),
            "encrypted": True,
            "signature": "sig123"
        }
        response = MessageResponse(**data)
        assert response.content == "Test message"
        assert response.user_nickname == "User1"
    
    def test_message_with_file(self):
        """Test mensaje con archivo"""
        data = {
            "id": "msg123",
            "content": "Archivo adjunto",
            "user_nickname": "User1",
            "room_id": "room123",
            "timestamp": datetime.now(),
            "encrypted": True,
            "signature": "abc123"
        }
        response = MessageResponse(**data)
        assert response.id == "msg123"
        assert response.content == "Archivo adjunto"


class TestTwoFactorSchemas:
    """Tests para schemas de 2FA"""
    
    def test_two_factor_setup_response(self):
        """Test respuesta de configuración 2FA"""
        data = {
            "secret": "JBSWY3DPEHPK3PXP",
            "qr_code": "otpauth://totp/...",
            "backup_codes": ["code1", "code2", "code3"]
        }
        response = TwoFactorSetupResponse(**data)
        assert len(response.backup_codes) == 3


class TestRoomType:
    """Tests para RoomType enum"""
    
    def test_room_types(self):
        """Test tipos de sala"""
        assert RoomType.TEXT == "text"
        assert RoomType.MULTIMEDIA == "multimedia"
    
    def test_room_type_values(self):
        """Test valores del enum"""
        values = [rt.value for rt in RoomType]
        assert "text" in values
        assert "multimedia" in values
