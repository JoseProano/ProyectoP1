"""
Script de configuración automática para crear sala de pruebas
"""
import requests
import sys

BACKEND_URL = "http://securechat_backend:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin123!@#"

def setup_room():
    try:
        # Login
        print("🔐 Autenticando como admin...")
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Error de autenticación: {response.status_code}")
            print(f"   {response.text}")
            return False
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Autenticación exitosa")
        
        # Primero verificar si la sala ya existe
        print("🔍 Verificando si LoadTestRoom ya existe...")
        response = requests.get(
            f"{BACKEND_URL}/api/rooms",
            headers=headers,
            timeout=10
        )
        
        room_id = None
        if response.status_code == 200:
            rooms = response.json()
            for room in rooms:
                if room.get("name") == "LoadTestRoom":
                    old_room_id = room.get("id")
                    print(f"⚠️  Sala LoadTestRoom encontrada, eliminando sala vieja...")
                    # Eliminar sala vieja
                    try:
                        delete_response = requests.delete(
                            f"{BACKEND_URL}/api/rooms/{old_room_id}",
                            headers=headers,
                            timeout=10
                        )
                        if delete_response.status_code == 200:
                            print(f"✅ Sala vieja eliminada")
                        else:
                            print(f"⚠️  No se pudo eliminar sala vieja (puede estar en uso)")
                    except:
                        pass
                    break
        
        # Crear sala nueva
        print("🏗️  Creando sala LoadTestRoom nueva...")
        response = requests.post(
            f"{BACKEND_URL}/api/rooms",
            headers=headers,
            json={
                "name": "LoadTestRoom",
                "pin": "1234",
                "room_type": "text",
                "description": "Sala automática para pruebas de carga",
                "max_users": 100
            },
            timeout=10
        )
        
        if response.status_code == 200:
            room_id = response.json().get("id")
            print(f"✅ Sala creada exitosamente (max 100 usuarios)")
            print(f"   Room ID: {room_id}")
        else:
            print(f"❌ Error al crear sala: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
        
        if not room_id:
            print("❌ No se pudo obtener room_id")
            return False
        
        # Actualizar locustfile
        print("📝 Actualizando locustfile.py...")
        import re
        with open('/loadtests/locustfile.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Reemplazar cualquier room_id existente (nuevo o placeholder)
        content = re.sub(
            r'room_id = "[^"]*"',
            f'room_id = "{room_id}"',
            content
        )
        
        with open('/loadtests/locustfile.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Locustfile actualizado con room_id: {room_id}")
        
        print("✅ Configuración completada exitosamente")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🏗️  Configurando sala de pruebas...\n")
    try:
        if setup_room():
            print("\n✅ Setup completado exitosamente")
            sys.exit(0)
        else:
            print("\n❌ Setup falló")
            print("💡 Verifica los logs para más detalles")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
