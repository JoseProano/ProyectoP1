"""
Script para crear la sala de pruebas necesaria para load testing
Ejecutar ANTES de iniciar las pruebas de carga
"""
import requests
import sys

def create_loadtest_room():
    """Crear sala LoadTestRoom para pruebas de carga"""
    print("🔧 Creando sala para pruebas de carga...")
    
    # Datos de la sala
    create_data = {
        "name": "LoadTestRoom",
        "password": "test123",
        "room_type": "text",
        "description": "Sala para pruebas de carga con Locust"
    }
    
    try:
        # Intentar crear la sala
        response = requests.post(
            "http://localhost:8000/api/rooms/create",
            json=create_data,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Sala 'LoadTestRoom' creada exitosamente")
            print("   Nombre: LoadTestRoom")
            print("   Password: test123")
            print("   Tipo: text")
            print("\n🚀 Ya puedes ejecutar las pruebas de carga:")
            print("   docker-compose --profile loadtest up loadtest")
            print("   O: locust -f locustfile.py --host=http://localhost:8000")
            return True
            
        elif response.status_code == 400:
            # Sala ya existe
            error_msg = response.json().get("detail", "")
            if "already exists" in error_msg.lower():
                print("ℹ️  La sala 'LoadTestRoom' ya existe (OK)")
                print("\n🚀 Ya puedes ejecutar las pruebas de carga:")
                print("   docker-compose --profile loadtest up loadtest")
                print("   O: locust -f locustfile.py --host=http://localhost:8000")
                return True
            else:
                print(f"❌ Error 400: {error_msg}")
                return False
                
        elif response.status_code == 401:
            print("⚠️  Se requiere autenticación de admin para crear salas")
            print("\n💡 Solución alternativa:")
            print("   1. Abre http://localhost:3000")
            print("   2. Inicia sesión como admin")
            print("   3. Crea una sala con:")
            print("      - Nombre: LoadTestRoom")
            print("      - Password: test123")
            print("      - Tipo: text")
            return False
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al backend en http://localhost:8000")
        print("\n💡 Asegúrate de que los contenedores estén corriendo:")
        print("   docker-compose up -d")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def verify_room_exists():
    """Verificar que la sala existe y es accesible"""
    print("\n🔍 Verificando acceso a la sala...")
    
    # Primero necesitamos obtener el room_id
    print("⚠️  IMPORTANTE: Necesitas el room_id de la sala LoadTestRoom")
    print("\nPara obtener el room_id:")
    print("1. Abre http://localhost:3000")
    print("2. Crea una sala llamada 'LoadTestRoom' con PIN 'test123'")
    print("3. Abre las DevTools del navegador (F12)")
    print("4. Ve a la pestaña Network")
    print("5. Crea o únete a la sala")
    print("6. Busca la request 'create' o 'join'")
    print("7. Copia el 'room_id' de la respuesta")
    print("8. Pega ese room_id en locustfile.py línea ~45")
    print("   Reemplaza: room_id = \"REPLACE_WITH_REAL_ROOM_ID\"")
    
    return False

def main():
    print("=" * 70)
    print("  CONFIGURACIÓN DE SALA PARA PRUEBAS DE CARGA - SECURECHAT")
    print("=" * 70)
    print()
    
    # Crear sala
    if create_loadtest_room():
        # Verificar
        if verify_room_exists():
            print("\n" + "=" * 70)
            print("  ✅ TODO LISTO PARA PRUEBAS DE CARGA")
            print("=" * 70)
            sys.exit(0)
    
    print("\n" + "=" * 70)
    print("  ⚠️  CONFIGURACIÓN INCOMPLETA")
    print("=" * 70)
    print("\n💡 Crea la sala manualmente desde la interfaz web:")
    print("   1. http://localhost:3000")
    print("   2. Login como admin (admin / Admin123!@#)")
    print("   3. Crear sala: LoadTestRoom / test123")
    sys.exit(1)

if __name__ == "__main__":
    main()
