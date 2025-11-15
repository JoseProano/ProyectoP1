"""
Automatización completa de pruebas de carga
1. Login como admin
2. Crear sala de pruebas
3. Obtener room_id
4. Ejecutar Locust
5. Limpiar (opcional)
"""
import requests
import subprocess
import sys
import time
import os

BACKEND_URL = "http://localhost:8000"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Admin123!@#"

class LoadTestAutomation:
    def __init__(self):
        self.admin_token = None
        self.room_id = None
        self.room_pin = "test123"
        
    def login_admin(self):
        """Login como administrador"""
        print("🔐 Autenticando como administrador...")
        
        try:
            response = requests.post(
                f"{BACKEND_URL}/api/admin/login",
                json={
                    "username": ADMIN_USERNAME,
                    "password": ADMIN_PASSWORD
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.admin_token = data.get("access_token")
                print("✅ Autenticación exitosa")
                return True
            else:
                print(f"❌ Error de autenticación: {response.status_code}")
                print(f"   {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error conectando al backend: {e}")
            print("💡 ¿Están corriendo los contenedores? docker-compose ps")
            return False
    
    def create_test_room(self):
        """Crear sala de pruebas"""
        print("\n🏗️  Creando sala de pruebas...")
        
        if not self.admin_token:
            print("❌ No hay token de admin")
            return False
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.post(
                f"{BACKEND_URL}/api/rooms/create",
                headers=headers,
                json={
                    "name": "LoadTestRoom",
                    "pin": self.room_pin,
                    "room_type": "text",
                    "description": "Sala automática para pruebas de carga"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.room_id = data.get("room_id")
                print(f"✅ Sala creada exitosamente")
                print(f"   Room ID: {self.room_id}")
                print(f"   PIN: {self.room_pin}")
                return True
            elif response.status_code == 400:
                # Sala ya existe, intentar obtener su ID
                print("⚠️  Sala ya existe, intentando obtener ID...")
                return self.get_existing_room_id()
            else:
                print(f"❌ Error creando sala: {response.status_code}")
                print(f"   {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def get_existing_room_id(self):
        """Obtener room_id de sala existente"""
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.get(
                f"{BACKEND_URL}/api/rooms/list",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                rooms = response.json()
                for room in rooms:
                    if room.get("name") == "LoadTestRoom":
                        self.room_id = room.get("room_id")
                        print(f"✅ Sala encontrada")
                        print(f"   Room ID: {self.room_id}")
                        return True
                
                print("❌ Sala LoadTestRoom no encontrada en la lista")
                return False
            else:
                print(f"❌ Error listando salas: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def update_locustfile(self):
        """Actualizar locustfile.py con el room_id correcto"""
        print(f"\n📝 Actualizando configuración de Locust...")
        
        locustfile_path = os.path.join(os.path.dirname(__file__), "locustfile.py")
        
        try:
            with open(locustfile_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Reemplazar el room_id
            updated_content = content.replace(
                'room_id = "REPLACE_WITH_REAL_ROOM_ID"',
                f'room_id = "{self.room_id}"'
            )
            
            with open(locustfile_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print("✅ Configuración actualizada")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando locustfile: {e}")
            return False
    
    def run_locust(self, mode="web", users=50, spawn_rate=10, run_time="5m"):
        """Ejecutar Locust"""
        print(f"\n🚀 Iniciando Locust ({mode} mode)...")
        
        if mode == "web":
            print("\n" + "="*70)
            print("  LOCUST WEB UI INICIADO")
            print("="*70)
            print(f"\n🌐 Abre tu navegador en: http://localhost:8089")
            print(f"\n⚙️  Configuración sugerida:")
            print(f"   - Number of users: {users}")
            print(f"   - Spawn rate: {spawn_rate}")
            print(f"   - Host: {BACKEND_URL}")
            print(f"\n📊 Cuando termines, presiona Ctrl+C para detener")
            print("="*70 + "\n")
            
            try:
                subprocess.run([
                    "locust",
                    "-f", "locustfile.py",
                    f"--host={BACKEND_URL}"
                ], cwd=os.path.dirname(__file__))
            except KeyboardInterrupt:
                print("\n\n⏹️  Locust detenido")
        else:
            # Modo headless
            print(f"   Users: {users}")
            print(f"   Spawn rate: {spawn_rate}/seg")
            print(f"   Duration: {run_time}")
            
            subprocess.run([
                "locust",
                "-f", "locustfile.py",
                f"--host={BACKEND_URL}",
                "--users", str(users),
                "--spawn-rate", str(spawn_rate),
                "--run-time", run_time,
                "--headless"
            ], cwd=os.path.dirname(__file__))
    
    def cleanup(self):
        """Eliminar sala de pruebas (opcional)"""
        print("\n🧹 ¿Deseas eliminar la sala de pruebas? (s/n): ", end="")
        choice = input().lower()
        
        if choice != 's':
            print("ℹ️  Sala mantenida para futuras pruebas")
            return
        
        if not self.admin_token or not self.room_id:
            print("⚠️  No hay sala para eliminar")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = requests.delete(
                f"{BACKEND_URL}/api/rooms/{self.room_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                print("✅ Sala eliminada exitosamente")
            else:
                print(f"⚠️  No se pudo eliminar sala: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error eliminando sala: {e}")

def main():
    print("="*70)
    print("  AUTOMATIZACIÓN DE PRUEBAS DE CARGA - SECURECHAT")
    print("="*70)
    
    automation = LoadTestAutomation()
    
    # 1. Login
    if not automation.login_admin():
        sys.exit(1)
    
    # 2. Crear/obtener sala
    if not automation.create_test_room():
        sys.exit(1)
    
    # 3. Actualizar locustfile
    if not automation.update_locustfile():
        sys.exit(1)
    
    # 4. Preguntar modo de ejecución
    print("\n" + "="*70)
    print("  MODO DE EJECUCIÓN")
    print("="*70)
    print("1. Web UI (interfaz gráfica) - Recomendado")
    print("2. Headless (sin interfaz, resultados en terminal)")
    print("\nElige una opción (1/2): ", end="")
    
    mode_choice = input().strip()
    
    if mode_choice == "2":
        print("\n⚙️  Configuración:")
        users = input("Número de usuarios (default: 50): ").strip() or "50"
        spawn_rate = input("Spawn rate/seg (default: 10): ").strip() or "10"
        run_time = input("Duración (ej: 5m, 10m) (default: 5m): ").strip() or "5m"
        
        automation.run_locust(
            mode="headless",
            users=int(users),
            spawn_rate=int(spawn_rate),
            run_time=run_time
        )
    else:
        automation.run_locust(mode="web")
    
    # 5. Cleanup (opcional)
    automation.cleanup()
    
    print("\n" + "="*70)
    print("  ✅ PRUEBAS COMPLETADAS")
    print("="*70)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Proceso interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
