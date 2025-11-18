# 🔒 Sistema de Chat Seguro en Tiempo Real

## 📋 Descripción

Sistema de chat en tiempo real con salas seguras que implementa las propiedades fundamentales de software seguro según los principios OWASP y NIST:

### 🔑 Características de Seguridad Implementadas

- **Confidencialidad**: 
  - **🔐 Encriptación E2E Real (True End-to-End)**: 
    * Mensajes encriptados en el navegador del emisor ANTES de enviar
    * Clave única por sala derivada de `room_id + PIN` usando PBKDF2 (10,000 iteraciones)
    * AES-256-CBC en el cliente con CryptoJS
    * El servidor NUNCA ve el contenido en claro (solo transmite cifrado)
    * Desencriptación solo en el navegador del receptor
  - TLS/SSL en producción para el transporte
- **Integridad**: Firmas digitales HMAC-SHA256, detección de esteganografía en imágenes
- **Disponibilidad**: Manejo de concurrencia con Redis, rate limiting, pruebas de carga para 100+ usuarios
- **Autenticación**: JWT con refresh tokens, bcrypt para contraseñas
- **Autorización**: Control de acceso basado en roles (Admin/User), validación de sesiones
- **No Repudio**: Logs inmutables con blockchain-like hash chaining y firmas digitales

### 🎨 Características de Interfaz

- **Diseño Responsive**: 
  - Interfaz adaptable a dispositivos móviles, tablets y desktop
  - Breakpoints: 320px, 480px, 768px, 1024px
  - Sin scroll horizontal en ningún dispositivo
  - Touch-friendly con tap targets de 44px mínimo
  - Fuentes fluidas con `clamp()` para legibilidad en todas las pantallas
  - Modo landscape optimizado para móviles
- **UX Optimizada**: 
  - Botones de ancho completo en móviles para fácil interacción
  - Overflow controlado con `word-break` para URLs largas
  - Layout vertical automático en pantallas pequeñas
  - Prevención de zoom en iOS con fuentes de 16px mínimo

## 🏗️ Arquitectura del Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                     CLIENTE (NAVEGADOR)                          │
│  ┌────────────────┐              ┌──────────────────┐           │
│  │  Admin Panel   │              │   Chat Client    │           │
│  │  (React)       │              │   (React)        │           │
│  └────────┬───────┘              └────────┬─────────┘           │
│           │ HTTP/REST + WebSocket         │                     │
└───────────┼──────────────────────────────┼──────────────────────┘
            │                              │
┌───────────▼──────────────────────────────▼──────────────────────┐
│                    BACKEND (FastAPI + Socket.IO)                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  API Gateway (CORS, Rate Limiting, JWT Auth)           │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│  ┌───────────────────────▼─────────────────────────────────┐   │
│  │  WebSocket Manager (Socket.IO)                          │   │
│  │  - Gestión de conexiones en tiempo real                 │   │
│  │  - Broadcasting de mensajes                             │   │
│  │  - Manejo de salas y usuarios                           │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│  ┌───────────────────────▼─────────────────────────────────┐   │
│  │  Servicios (Business Logic)                             │   │
│  │  - AuthService: Autenticación y tokens                  │   │
│  │  - RoomService: Gestión de salas                        │   │
│  │  - SessionService: Sesiones de usuarios                 │   │
│  │  - FileService: Subida segura de archivos               │   │
│  └───────────────────────┬─────────────────────────────────┘   │
│  ┌───────────────────────▼─────────────────────────────────┐   │
│  │  Utilidades de Seguridad                                │   │
│  │  - CryptoManager: AES-256-GCM encryption                │   │
│  │  - SteganographyDetector: Análisis de imágenes          │   │
│  │  - AuditLogger: Logs inmutables con firmas              │   │
│  └─────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼────────┐  ┌──────▼───────┐  ┌───────▼────────┐
│    MongoDB     │  │    Redis     │  │  File System   │
│   (Database)   │  │  (Sessions   │  │   (Uploads)    │
│   - Usuarios   │  │   & Cache)   │  │   - Imágenes   │
│   - Salas      │  │  - AOF       │  │   - Archivos   │
│   - Mensajes   │  │  Persistence │  │                │
└────────────────┘  └──────────────┘  └────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   LOAD TESTING (Locust)                         │
│  - Pruebas de carga para 50-100 usuarios simultáneos           │
│  - Limpieza automática de sesiones                             │
│  - Configuración automática de salas de prueba                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Inicio Rápido

### Requisitos Previos

- Docker y Docker Compose
- Navegador web moderno (Chrome, Firefox, Edge)
- Puerto 8000 (backend), 3000 (frontend), 8089 (load tests) disponibles

### Instalación con Docker (Recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/JoseProano/ProyectoP1.git
cd ProyectoP1

# 2. Iniciar todos los servicios
docker-compose up -d

# 3. Verificar que los servicios estén corriendo
docker-compose ps

# 4. Acceder a la aplicación
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
# Load Tests: http://localhost:8089
```

### Credenciales de Administrador

- **Usuario**: `admin`
- **Contraseña**: `Admin123!@#`

### Primer Uso

1. Accede a http://localhost:3000
2. Haz clic en "Administración" para crear salas
3. Inicia sesión con las credenciales de admin
4. Crea una sala nueva con PIN de 4-8 dígitos
5. Regresa a la página principal y únete a la sala

## 📁 Estructura del Proyecto

```
ProyectoP1/
├── backend/                      # API Backend (FastAPI + Socket.IO)
│   ├── app/
│   │   ├── models/              # Modelos Pydantic (schemas)
│   │   ├── services/            # Lógica de negocio
│   │   │   ├── auth_service.py      # Autenticación y JWT
│   │   │   ├── room_service.py      # Gestión de salas
│   │   │   ├── session_service.py   # Sesiones de usuarios (Redis)
│   │   │   └── file_service.py      # Subida segura de archivos
│   │   ├── utils/               # Utilidades
│   │   │   ├── crypto.py            # Encriptación AES-256-GCM
│   │   │   ├── logging.py           # Logs inmutables con firmas
│   │   │   ├── steganography.py     # Detector de esteganografía
│   │   │   └── rate_limiter.py      # Rate limiting
│   │   ├── config.py            # Configuración (variables de entorno)
│   │   ├── database.py          # Conexión a MongoDB
│   │   └── main.py              # App principal
│   ├── tests/                   # Tests unitarios (70% coverage)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend-react/               # Cliente React
│   ├── src/
│   │   ├── components/          # Componentes reutilizables
│   │   ├── pages/               # Páginas principales
│   │   ├── services/            # API y Socket.IO services
│   │   └── App.js
│   ├── package.json
│   └── Dockerfile
├── load_tests/                   # Pruebas de carga con Locust
│   ├── locustfile.py            # Definición de usuarios simulados
│   ├── auto_setup.py            # Configuración automática de salas
│   ├── cleanup.py               # Limpieza de sesiones
│   └── README.md                # Documentación de load testing
├── logs/                         # Logs de auditoría
│   ├── audit.log                # Log de todas las acciones
│   ├── security.log             # Alertas de seguridad
│   └── log_chain.json           # Cadena de hashes para verificación
├── docker-compose.yml            # Orquestación de servicios
├── ARCHITECTURE.md               # Diagrama de arquitectura detallado
├── VERIFICACION_FINAL_REQUISITOS.md  # Verificación final de requisitos del proyecto
└── README.md                     # Este archivo
```

## 🔑 Características de Seguridad

### 1. Autenticación y Autorización

- **Autenticación de Administradores**: bcrypt + JWT con refresh tokens
- **Acceso a Salas**: PIN encriptado con bcrypt (4-8 dígitos)
- **Sesiones Seguras**: Almacenadas en Redis con TTL configurable
- **Device Fingerprinting**: Un dispositivo por sala simultáneamente

### 2. Encriptación y Criptografía

- **🔐 E2E (End-to-End Encryption) - Verdadera Encriptación Cliente-a-Cliente**:
  - **Implementación**:
    * Mensajes encriptados en el navegador del emisor con AES-256-CBC
    * Clave única por sala derivada de `room_id + PIN` usando PBKDF2 (10,000 iteraciones)
    * Salt aleatorio generado por CryptoJS para cada mensaje
    * Formato: `U2FsdGVkX1+...` (Base64 del cipher)
  - **Flujo de Encriptación**:
    1. Usuario ingresa a sala con PIN
    2. Cliente genera clave: `PBKDF2(room_id + PIN, salt, 10000 iterations)`
    3. Clave almacenada en `sessionStorage` (no persiste entre sesiones)
    4. Mensaje se encripta ANTES de `socket.emit('send_message')`
    5. Servidor recibe `encrypted_content` y lo almacena en MongoDB SIN desencriptar
    6. Servidor transmite `encrypted_content` a receptores
    7. Receptores desencriptan con su clave local
  - **Verificación**: 
    * MongoDB muestra `encrypted_content: "U2FsdGVkX1+..."`
    * Logs del servidor: `"[DEBUG] Returning X E2E encrypted messages (server cannot read)"`
    * Consola del navegador: `"🔐 E2E encryption key generated for room"`
- **Claves de Sala**: Generadas automáticamente al unirse con el PIN, no compartidas con el servidor
- **TLS/SSL**: En producción para tráfico HTTPS/WSS (protección del canal)
- **Bcrypt**: Para contraseñas de admin y PINs de salas (cost factor 12)

### 3. Integridad y No Repudio

- **Logs Inmutables**: Blockchain-like hash chaining
- **Firmas Digitales**: HMAC-SHA256 en cada entrada de log
- **Verificación**: Endpoint `/api/logs/verify` para validar integridad
- **Timestamps**: Con zona horaria de Ecuador (America/Guayaquil)

### 4. Detección de Amenazas

- **Esteganografía**: Análisis de imágenes subidas (LSB, DCT, metadata)
- **Rate Limiting**: 
  - **HTTP Endpoints**: 30 requests/minuto por IP
  - **WebSocket Messages**: 30 mensajes/minuto por sesión
- **Validación de Entrada**: Pydantic schemas con sanitización
- **XSS Protection**: Escape de HTML en nicknames y mensajes

### 5. Disponibilidad y Rendimiento

- **Redis con AOF**: Persistencia de sesiones entre reinicios
- **Load Testing**: Soporta 50-100 usuarios concurrentes
- **Cleanup Automático**: Limpieza de sesiones al detener tests
- **Concurrent Users**: Manejo de múltiples usuarios por sala

## 🧪 Testing

### Tests Unitarios

```bash
# Ejecutar tests con coverage
docker exec securechat_backend pytest --cov=app --cov-report=html --cov-report=term

# Ver reporte de cobertura (70% actual)
# Abre htmlcov/index.html en el navegador
```

**Cobertura actual**: 70% (229 tests pasando)

### Pruebas de Carga

```bash
# Acceder a la interfaz de Locust
http://localhost:8089

# Configuración recomendada:
# - Number of users: 50-100
# - Spawn rate: 10
# - Host: http://securechat_backend:8000
```

**Características del Load Testing:**
- Configuración automática de sala de pruebas
- 2 tipos de usuarios simulados (Heavy/Light)
- Soporte para 100 usuarios simultáneos por sala

## 📊 Logs y Auditoría

### Ver Logs en Tiempo Real

```powershell
# Logs del contenedor
docker logs securechat_backend -f

# Logs de auditoría (dentro del contenedor)
docker exec securechat_backend tail -f /app/logs/audit.log

# Logs de seguridad
docker exec securechat_backend tail -f /app/logs/security.log
```

### Copiar Logs a tu Máquina

```powershell
docker cp securechat_backend:/app/logs/audit.log .\logs\
docker cp securechat_backend:/app/logs/security.log .\logs\
docker cp securechat_backend:/app/logs/log_chain.json .\logs\
```

### Verificar Integridad

```bash
# Verificar cadena de hashes
curl http://localhost:8000/api/logs/verify
```

## 📱 Diseño Responsive

### Características Implementadas

- **Viewport Control Global**:
  ```css
  * { box-sizing: border-box; }
  html, body { overflow-x: hidden; }
  ```
- **Breakpoints Responsive**:
  - **≤ 480px**: Móviles pequeños (iPhone SE, Android compactos)
    * Layout completamente vertical
    * Botones de ancho completo
    * Padding reducido (8-10px)
    * Fuentes: 12-14px
  - **≤ 768px**: Móviles y tablets pequeñas
    * Headers verticales
    * Sidebars colapsados o apilados
    * Touch targets de 44px mínimo
  - **≤ 1024px**: Tablets y pantallas medianas
    * Grids de 2 columnas
    * Padding moderado
  - **> 1024px**: Desktop
    * Layout completo horizontal
    * Grids de 3+ columnas

- **Optimizaciones Móviles**:
  - `clamp()` para fuentes fluidas: `clamp(16px, 4vw, 24px)`
  - `100dvh` para altura en móviles (respeta barra de navegación)
  - `word-wrap: break-word` para URLs largas
  - Prevención de zoom en iOS: `font-size: 16px` en inputs
  - Sin scroll horizontal: `max-width: 100vw`, `overflow-x: hidden`

- **Componentes Adaptables**:
  - **AdminDashboard**: Header vertical en móvil, botones stacked
  - **ChatRoom**: Sidebar colapsado, mensajes 85-92% ancho en móvil
  - **Forms**: Labels arriba, inputs full-width
  - **Modals**: 95% ancho en móvil, padding reducido

### Pruebas de Responsive

```bash
# 1. Abrir DevTools (F12)
# 2. Toggle Device Toolbar (Ctrl+Shift+M)
# 3. Probar anchos:
#    - 320px (iPhone SE)
#    - 375px (iPhone X)
#    - 414px (iPhone Plus)
#    - 500px (Custom)
#    - 768px (iPad)
#    - 1024px (iPad Pro)

# Verificar:
# ✓ No hay scroll horizontal
# ✓ Todos los botones visibles
# ✓ Texto legible sin zoom
# ✓ Tap targets > 44px
```

## 🔧 Configuración

### Variables de Entorno (docker-compose.yml)

```yaml
backend:
  environment:
    - MONGODB_URL=mongodb://mongodb:27017
    - REDIS_HOST=redis
    - SECRET_KEY=your-super-secret-key-change-in-production-fixed-key-2025
    - AES_KEY=aes-encryption-key-fixed-for-persistence-2025-secure
    - ENCRYPTION_KEY=encryption-key-fixed-for-message-persistence-2025
    - ADMIN_USERNAME=admin
    - ADMIN_PASSWORD=Admin123!@#
```

**⚠️ IMPORTANTE**: Cambia estas claves en producción

### Persistencia de Datos

- **MongoDB**: Volumen `mongodb_data` para base de datos
- **Redis AOF**: Persistencia append-only activada
- **Logs**: Montados en `./logs`
- **Uploads**: Almacenados en volumen `uploads_data`

## 🌐 Despliegue en Producción

Ver [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) para instrucciones detalladas.

**Checklist de Producción:**
- [ ] Cambiar todas las claves secretas
- [ ] Configurar TLS/SSL (HTTPS/WSS)
- [ ] Configurar backup de MongoDB
- [ ] Configurar backup de logs
- [ ] Revisar rate limits
- [ ] Configurar firewall
- [ ] Monitorear recursos (CPU, RAM, Disco)

## 📖 Documentación Adicional

- [ARCHITECTURE.md](ARCHITECTURE.md) - Diagrama de arquitectura detallado
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Guía de despliegue
- [QUICKSTART.md](QUICKSTART.md) - Guía rápida de inicio
- [load_tests/README.md](load_tests/README.md) - Documentación de load testing

## 🛠️ Comandos Útiles

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener servicios
docker-compose down

# Reiniciar un servicio
docker-compose restart backend

# Reconstruir un servicio
docker-compose build backend
docker-compose up -d backend

# Limpiar Redis (sesiones)
docker exec securechat_redis redis-cli FLUSHALL

# Acceder al shell de MongoDB
docker exec -it securechat_mongodb mongosh

# Ver estadísticas de Redis
docker exec securechat_redis redis-cli INFO
```

## 🐛 Troubleshooting

### Los usuarios de load testing no se desconectan

```bash
# Limpiar manualmente Redis
docker exec securechat_redis redis-cli FLUSHALL

# Reiniciar loadtest
docker-compose restart loadtest
```

### Mensajes no persisten después de reiniciar

Verifica que las claves de encriptación sean fijas en `docker-compose.yml`:
```yaml
- AES_KEY=aes-encryption-key-fixed-for-persistence-2025-secure
- ENCRYPTION_KEY=encryption-key-fixed-for-message-persistence-2025
```

### Error de conexión a MongoDB/Redis

```bash
# Verificar que los servicios estén corriendo
docker-compose ps

# Reiniciar servicios de base de datos
docker-compose restart mongodb redis
```

## 📝 Licencia

Este proyecto es parte de un trabajo académico para las materias de Aplicaciones Distribuidas y Desarrollo de Software Seguro.

## 👥 Autor

Proyecto desarrollado como parte de los cursos de Apliaciones Distribuidas / Desarrollo de Software Seguro.

---

**Última actualización**: Noviembre 2025
