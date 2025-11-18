"""
Script para probar la detección de esteganografía vía API
"""
import requests
import json

# Configuración
BASE_URL = "http://localhost:8000"

print("=" * 70)
print("PRUEBA DE DETECCIÓN DE ESTEGANOGRAFÍA - API")
print("=" * 70)

# 1. Primero crear un admin y obtener token
print("\n1️⃣ Creando sesión de admin...")
try:
    response = requests.post(
        f"{BASE_URL}/auth/admin/login",
        json={"username": "admin", "password": "Admin123!@#"}
    )
    if response.status_code == 200:
        token = response.json()['access_token']
        print(f"   ✅ Token obtenido: {token[:20]}...")
    else:
        print(f"   ❌ Error: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# 2. Crear una sala
print("\n2️⃣ Creando sala de prueba...")
try:
    response = requests.post(
        f"{BASE_URL}/rooms/create",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Prueba Stego", "max_members": 10}
    )
    if response.status_code == 200:
        room_data = response.json()
        room_id = room_data['room_id']
        room_code = room_data['room_code']
        print(f"   ✅ Sala creada: {room_id}")
        print(f"   📋 Código: {room_code}")
    else:
        print(f"   ❌ Error: {response.status_code} - {response.text}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# 3. Subir la imagen sospechosa
print("\n3️⃣ Subiendo imagen con esteganografía (espe_test.png)...")
try:
    with open('espe_test.png', 'rb') as f:
        files = {'file': ('espe_test.png', f, 'image/png')}
        data = {'room_id': room_id}
        
        response = requests.post(
            f"{BASE_URL}/upload/multimedia",
            headers={"Authorization": f"Bearer {token}"},
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Respuesta del servidor:")
            print(json.dumps(result, indent=4))
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   📄 Respuesta: {response.text}")
            
            # Si fue rechazado por esteganografía, mostrar detalles
            if response.status_code == 400:
                error_data = response.json()
                if 'steganography_analysis' in error_data:
                    print("\n   🔍 ANÁLISIS DE ESTEGANOGRAFÍA:")
                    analysis = error_data['steganography_analysis']
                    print(f"      • Archivo: {analysis.get('filename')}")
                    print(f"      • Entropía: {analysis.get('file_entropy', 0):.4f}")
                    print(f"      • Entropía cola: {analysis.get('tail_entropy', 0):.4f}")
                    print(f"      • Nivel de amenaza: {analysis.get('threat_level', 'unknown').upper()}")
                    print(f"      • Razón: {analysis.get('reason')}")
                    print(f"\n   ✅ ¡DETECCIÓN FUNCIONANDO CORRECTAMENTE!")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 70)
