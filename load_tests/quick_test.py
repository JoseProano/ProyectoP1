"""
Script de prueba rápida para verificar configuración de Locust
Ejecutar: python quick_test.py
"""
import requests
import socketio
import time

def test_basic_connection():
    """Prueba conexión básica al servidor"""
    print("🔍 Probando conexión al servidor...")
    
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Servidor respondiendo correctamente")
            return True
        else:
            print(f"❌ Servidor respondió con status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error conectando al servidor: {e}")
        print("💡 Asegúrate de que los contenedores estén corriendo:")
        print("   docker-compose up -d")
        return False

def test_room_creation():
    """Prueba creación de sala para tests"""
    print("\n🔍 Probando creación de sala de pruebas...")
    
    try:
        create_data = {
            "name": "LoadTestRoom",
            "password": "test123",
            "room_type": "text",
            "description": "Sala para pruebas de carga"
        }
        
        response = requests.post(
            "http://localhost:8000/api/rooms/create",
            json=create_data,
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Sala de pruebas creada exitosamente")
            return True
        elif response.status_code == 400:
            print("ℹ️  Sala de pruebas ya existe (OK)")
            return True
        else:
            print(f"❌ Error creando sala: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_join_room():
    """Prueba unirse a sala"""
    print("\n🔍 Probando unirse a sala...")
    
    try:
        join_data = {
            "room_name": "LoadTestRoom",
            "room_password": "test123",
            "nickname": "TestUser",
            "device_fingerprint": "test_device_123"
        }
        
        response = requests.post(
            "http://localhost:8000/api/rooms/join",
            json=join_data,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Unido a sala exitosamente")
            print(f"   Session ID: {data.get('session_id', 'N/A')[:20]}...")
            print(f"   Room ID: {data.get('room_id', 'N/A')[:20]}...")
            return True
        else:
            print(f"❌ Error uniéndose a sala: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_websocket_connection():
    """Prueba conexión WebSocket"""
    print("\n🔍 Probando conexión WebSocket...")
    
    try:
        sio = socketio.Client(reconnection=False, logger=False, engineio_logger=False)
        
        @sio.on('connect')
        def on_connect():
            print("✅ WebSocket conectado exitosamente")
        
        @sio.on('connect_error')
        def on_connect_error(data):
            print(f"❌ Error de conexión WebSocket: {data}")
        
        sio.connect('http://localhost:8000', transports=['websocket'])
        time.sleep(1)
        
        if sio.connected:
            sio.disconnect()
            return True
        else:
            print("❌ No se pudo establecer conexión WebSocket")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Ejecutar todas las pruebas"""
    print("=" * 60)
    print("  PRUEBAS DE CONFIGURACIÓN - LOAD TESTING SECURECHAT")
    print("=" * 60)
    
    results = []
    
    # Ejecutar pruebas
    results.append(("Conexión al servidor", test_basic_connection()))
    results.append(("Creación de sala", test_room_creation()))
    results.append(("Unirse a sala", test_join_room()))
    results.append(("Conexión WebSocket", test_websocket_connection()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("  RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "-" * 60)
    print(f"Total: {passed}/{total} pruebas pasadas")
    
    if passed == total:
        print("\n🎉 ¡Todo listo para ejecutar pruebas de carga!")
        print("\n📝 Siguiente paso:")
        print("   locust -f locustfile.py --host=http://localhost:8000")
        print("   Luego abre: http://localhost:8089")
    else:
        print("\n⚠️  Corrige los errores antes de ejecutar pruebas de carga")
        print("\n💡 Comandos útiles:")
        print("   docker-compose up -d          # Iniciar contenedores")
        print("   docker-compose logs backend   # Ver logs del backend")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
