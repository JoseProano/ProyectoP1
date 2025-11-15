# Pruebas de Carga - SecureChat

## Descripción
Pruebas de carga con **Locust** para validar el soporte de **50+ usuarios simultáneos** por sala.

**Características:**
- ✅ Configuración automática de sala de pruebas
- ✅ Limpieza automática de sesiones Redis al detener
- ✅ Soporte para 100+ usuarios concurrentes
- ✅ Device fingerprint opcional para múltiples usuarios desde un contenedor
- ✅ Trap SIGTERM/SIGINT para cleanup on stop

## 🚀 Inicio Rápido (Automatizado)

### Opción 1: Script Automatizado (Recomendado)
```powershell
cd load_tests
pip install -r requirements.txt
python run_loadtest.py
```

Este script:
1. ✅ Se autentica como admin automáticamente
2. ✅ Crea la sala de pruebas (o usa una existente)
3. ✅ Obtiene el room_id automáticamente
4. ✅ Configura Locust
5. ✅ Ejecuta las pruebas
6. ✅ Opcionalmente elimina la sala al terminar

### Opción 2: Ejecución con Docker (Automatizado y Recomendado)

El proyecto incluye configuración completa de Docker con:
- ✅ Configuración automática de sala de pruebas (`auto_setup.py`)
- ✅ Limpieza automática de sesiones al detener tests (`cleanup.py`)
- ✅ Room ID actualizado automáticamente en `locustfile.py`

#### Iniciar contenedor de pruebas de carga
```powershell
# Desde la raíz del proyecto
docker-compose up -d loadtest
```

#### Acceder a Locust Web UI
Abre en tu navegador: **http://localhost:8089**

**Configuración sugerida:**
- Number of users: 50-100
- Spawn rate: 10 (usuarios/segundo)
- Host: **http://securechat_backend:8000** (ya configurado)

**Características automáticas:**
- La sala "LoadTestRoom" se crea automáticamente si no existe
- El `room_id` se obtiene y actualiza en `locustfile.py`
- Al detener las pruebas (STOP o Ctrl+C), se ejecuta cleanup automático

#### Ver logs
```powershell
docker logs -f securechat_loadtest
```

#### Detener pruebas
```powershell
# Detener contenedor (activa cleanup automático)
docker-compose stop loadtest

# O detener todo el stack
docker-compose down
```

### Modo Headless (sin interfaz)
```powershell
# 50 usuarios, 10/seg, 5 minutos
docker-compose run --rm loadtest locust -f locustfile.py --host=http://securechat_backend:8000 --users 50 --spawn-rate 10 --run-time 5m --headless

# 100 usuarios, 20/seg, 10 minutos
docker-compose run --rm loadtest locust -f locustfile.py --host=http://securechat_backend:8000 --users 100 --spawn-rate 20 --run-time 10m --headless
```

## Opción 2: Instalación Local

```powershell
cd load_tests
pip install -r requirements.txt
```

## Ejecutar Pruebas

### Modo Web UI (Recomendado)
```powershell
locust -f locustfile.py --host=http://localhost:8000
```

Luego abre: http://localhost:8089

**Configuración sugerida:**
- Number of users: 50-100
- Spawn rate: 10 (usuarios/segundo)
- Host: http://localhost:8000

### Modo Headless (Sin interfaz)
```powershell
# 50 usuarios, spawn rate 10/seg, duración 5 minutos
locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 10 --run-time 5m --headless

# 100 usuarios, spawn rate 20/seg, duración 10 minutos
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 20 --run-time 10m --headless
```

## Tipos de Usuarios

### SecureChatUser (Base)
- Usuario estándar
- Envía mensajes cada 1-3 segundos
- Realiza consultas de historial

### HeavyLoadUser (Carga Pesada)
- 25% de usuarios
- Envía mensajes cada 0.5-1.5 segundos
- Simula usuarios muy activos

### LightLoadUser (Carga Ligera)
- 75% de usuarios  
- Envía mensajes cada 3-8 segundos
- Simula usuarios que mayormente observan

## Tareas Simuladas

| Tarea | Peso | Descripción |
|-------|------|-------------|
| `send_message` | 3 | Enviar mensaje via WebSocket |
| `get_room_messages` | 1 | Obtener historial de mensajes |
| `check_session_activity` | 1 | Actualizar actividad de sesión |

## Métricas Monitoreadas

- **Requests per second (RPS)**: Solicitudes por segundo
- **Response time**: Tiempo de respuesta (p50, p95, p99)
- **Failure rate**: Tasa de fallos
- **Concurrent users**: Usuarios concurrentes
- **WebSocket connections**: Conexiones activas

## Escenarios de Prueba

### Prueba Básica - 50 Usuarios
```powershell
locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 10 --run-time 5m --headless
```

### Prueba de Estrés - 100 Usuarios
```powershell
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 20 --run-time 10m --headless
```

### Prueba de Escalabilidad - 200 Usuarios
```powershell
locust -f locustfile.py --host=http://localhost:8000 --users 200 --spawn-rate 25 --run-time 15m --headless
```

## Resultados Esperados

### ✅ Criterios de Éxito
- **RPS**: > 100 requests/seg
- **Response time p95**: < 500ms
- **Failure rate**: < 1%
- **WebSocket connections**: 50+ simultáneas estables
- **Message delivery**: < 200ms latencia

### ⚠️ Señales de Advertencia
- Response time p95 > 1000ms
- Failure rate > 5%
- Desconexiones frecuentes de WebSocket
- Pérdida de mensajes

## Monitoreo Durante Pruebas

### Ver logs del backend
```powershell
docker logs -f securechat_backend
```

### Ver métricas de MongoDB
```powershell
docker exec -it securechat_mongodb mongosh -u admin -p securepassword123 --authenticationDatabase admin --eval "db.serverStatus()"
```

### Ver métricas de Redis
```powershell
docker exec securechat_redis redis-cli INFO stats
```

## Troubleshooting

### Error: "Connection refused"
- Verifica que los contenedores estén corriendo: `docker-compose ps`
- Reinicia: `docker-compose restart`

### Error: "Too many WebSocket connections"
- Aumenta límites en el backend
- Reduce spawn rate

### Mensajes no se envían
- Verifica que la sala "LoadTestRoom" existe
- Revisa logs del backend para errores

### Los usuarios no se desconectan al detener las pruebas
**Solución implementada**: Mecanismo automático de cleanup

El proyecto incluye un sistema de limpieza automática de sesiones Redis cuando detienes las pruebas:

1. **cleanup.py**: Script que ejecuta `FLUSHALL` en Redis para limpiar todas las sesiones
2. **docker-entrypoint.sh**: Tiene un trap para SIGTERM/SIGINT que llama a cleanup.py
3. **locustfile.py**: Implementa `on_stop()` que emite evento `leave_room_ws` al detener usuarios

**Proceso de limpieza:**
```bash
# Cuando detienes las pruebas (Ctrl+C o STOP en UI):
1. Locust detiene todos los usuarios
2. Cada usuario ejecuta on_stop() → emite leave_room_ws
3. El trap en docker-entrypoint.sh detecta SIGTERM/SIGINT
4. Se ejecuta cleanup.py → Redis FLUSHALL
5. Todas las sesiones se eliminan
```

**Limpieza manual (si es necesario):**
```powershell
# Limpiar todas las sesiones de Redis
docker exec securechat_redis redis-cli FLUSHALL

# Reiniciar contenedor loadtest
docker-compose restart loadtest

# Ver sesiones activas en Redis
docker exec securechat_redis redis-cli KEYS "session:*"
```

## Generar Reporte

```powershell
# Guardar estadísticas en CSV
locust -f locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 10 --run-time 5m --headless --csv=results/test_report

# Esto genera:
# - results/test_report_stats.csv
# - results/test_report_stats_history.csv
# - results/test_report_failures.csv
```

## Arquitectura de Hilos

Locust usa **gevent** para manejar miles de usuarios concurrentes con hilos verdes (greenlets):

- Cada usuario = 1 greenlet (thread ligero)
- Soporte para miles de usuarios en una sola máquina
- Escalable horizontalmente con múltiples workers

### Modo Distribuido (Múltiples CPUs)

**Master:**
```powershell
locust -f locustfile.py --master --host=http://localhost:8000
```

**Workers (en otras terminales):**
```powershell
locust -f locustfile.py --worker
locust -f locustfile.py --worker
locust -f locustfile.py --worker
```

Esto permite escalar a 1000+ usuarios usando todos los cores del CPU.
