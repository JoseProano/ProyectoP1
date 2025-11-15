#!/usr/bin/env python3
"""
Script de limpieza para eliminar todas las sesiones de la sala de pruebas
cuando Locust termina o se detiene
"""
import os
import sys
import redis

def cleanup_test_room():
    """Limpia todas las sesiones de Redis"""
    try:
        # Conectar a Redis
        redis_host = os.getenv("REDIS_HOST", "securechat_redis")
        r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
        
        print("\n🧹 Limpiando sesiones de prueba...")
        
        # Limpiar todas las sesiones
        session_keys = r.keys("session:*")
        if session_keys:
            deleted = r.delete(*session_keys)
            print(f"✅ {deleted} sesiones eliminadas")
        else:
            print("ℹ️  No hay sesiones para limpiar")
        
        # Limpiar contadores de salas
        room_keys = r.keys("session:room:*")
        if room_keys:
            r.delete(*room_keys)
            print(f"✅ Contadores de sala limpiados")
        
        # Limpiar dispositivos
        device_keys = r.keys("session:device:*")
        if device_keys:
            r.delete(*device_keys)
            print(f"✅ Dispositivos limpiados")
        
        print("✅ Limpieza completada - sala lista para nuevas pruebas\n")
        return True
        
    except Exception as e:
        print(f"❌ Error durante limpieza: {e}")
        return False

if __name__ == "__main__":
    cleanup_test_room()
