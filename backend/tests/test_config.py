"""
Tests adicionales para aumentar cobertura a 70%+
"""
import pytest
from app.config import settings


class TestConfigSettings:
    """Tests para configuración"""
    
    def test_settings_initialized(self):
        """Test que settings está inicializado"""
        assert settings is not None
        assert hasattr(settings, 'SECRET_KEY')
        assert hasattr(settings, 'ALGORITHM')
        assert hasattr(settings, 'MONGODB_URL')
        assert hasattr(settings, 'REDIS_URL')
    
    def test_security_settings(self):
        """Test configuraciones de seguridad"""
        assert len(settings.SECRET_KEY) > 0
        assert settings.ALGORITHM in ['HS256', 'RS256']
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
    
    def test_database_settings(self):
        """Test configuraciones de base de datos"""
        assert 'mongodb' in settings.MONGODB_URL.lower()
        assert 'redis' in settings.REDIS_URL.lower()
