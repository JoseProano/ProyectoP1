# Arquitectura del Sistema de Chat Seguro

## 📐 Diagrama de Arquitectura General

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
│  │  - SessionService: Sesiones de usuarios (Redis)         │   │
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
│  - Limpieza automática de sesiones con Redis FLUSHALL          │
│  - Configuración automática de salas de prueba (auto_setup.py) │
│  - Trap SIGTERM/SIGINT para cleanup on stop                    │
└─────────────────────────────────────────────────────────────────┘
```

## 🔐 Capas de Seguridad

### 1. Capa de Transporte
- **TLS/SSL**: Encriptación en tránsito
- **HTTPS**: Forzado en producción
- **WebSocket Secure (WSS)**: Para comunicación en tiempo real

### 2. Capa de Autenticación
```
Usuario/Admin
    │
    ▼
┌────────────────────┐
│  Credenciales      │
│  (user + pass)     │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Password Hash     │
│  (bcrypt)          │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  2FA Verification  │
│  (TOTP - opcional) │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  JWT Token         │
│  (signed)          │
└────────────────────┘
```

### 3. Capa de Encriptación
```
Datos en Reposo:
├── AES-256-GCM (mensajes)
├── bcrypt (contraseñas, PINs)
└── SHA-256 (hashes de archivos)

Datos en Tránsito:
├── TLS 1.3
└── End-to-End Encryption (mensajes)
```

### 4. Capa de Integridad
```
┌──────────────────────┐
│  Acción del Usuario  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Generar Log Entry   │
│  (timestamp + datos) │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Firma Digital       │
│  (HMAC-SHA256)       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Hash con Cadena     │
│  (previous_hash)     │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Append to Log File  │
│  (inmutable)         │
└──────────────────────┘
```

## 🔍 Flujo de Detección de Esteganografía

```
Archivo Subido
    │
    ▼
┌──────────────────────┐
│  Validar Tipo MIME   │
│  y Tamaño            │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│  Calcular Entropía   │
│  Shannon (bytes)     │
└─────────┬────────────┘
          │
          ▼           
    ┌─────┴─────┐
    │ Entropía  │
    │  > 7.5?   │
    └─────┬─────┘
          │ No
          ▼
┌──────────────────────┐
│  Análisis LSB        │
│  (si es imagen)      │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│  Test Chi-cuadrado   │
└─────────┬────────────┘
          │
          ▼
┌──────────────────────┐
│  Análisis Metadatos  │
│  (EXIF, etc.)        │
└─────────┬────────────┘
          │
          ▼
    ┌─────┴─────┐
    │ ¿Sospechoso?│
    └─────┬─────┘
    Sí    │    No
    │     │     │
    ▼     │     ▼
┌────────┐│  ┌────────┐
│Rechazar││  │Aceptar │
│+ Alerta││  │+ Guardar│
└────────┘│  └────────┘
          │
          ▼
    [Fin del flujo]
```

## 🧵 Manejo de Concurrencia

### ThreadPoolExecutor para Operaciones Pesadas
```python
# Análisis de archivos en paralelo
executor = ThreadPoolExecutor(max_workers=4)
future = executor.submit(analyze_file, file_bytes)
result = future.result()
```

### Operaciones Asíncronas con asyncio
```python
# Base de datos y Redis
await db.collection.find_one(query)
await session_store.create_session(...)
```

### WebSocket Concurrente
```python
# Socket.IO maneja automáticamente múltiples conexiones
@sio.event
async def send_message(sid, data):
    # Procesado en thread separado
    await sio.emit('new_message', data, room=room_id)
```

## 📊 Modelo de Datos

### MongoDB Collections

#### admins
```javascript
{
  "_id": ObjectId,
  "username": String (unique),
  "email": String (unique),
  "password_hash": String (bcrypt),
  "role": "admin",
  "two_factor_enabled": Boolean,
  "two_factor_secret": String?,
  "backup_codes": [String],
  "created_at": DateTime,
  "last_login": DateTime?,
  "is_active": Boolean
}
```

#### rooms
```javascript
{
  "_id": ObjectId,
  "room_id": String (unique, encrypted),
  "name": String,
  "room_type": "text" | "multimedia",
  "description": String?,
  "pin_hash": String (bcrypt),
  "max_users": Number,
  "created_by": String (admin_id),
  "created_by_username": String,
  "created_at": DateTime,
  "is_active": Boolean,
  "total_messages": Number,
  "total_files": Number
}
```

#### messages
```javascript
{
  "_id": ObjectId,
  "room_id": String (indexed),
  "user_id": String,
  "content": String (encrypted),
  "encrypted": Boolean,
  "timestamp": DateTime (indexed),
  "signature": String (HMAC)
}
```

#### files
```javascript
{
  "_id": ObjectId,
  "file_id": String (unique),
  "filename": String,
  "room_id": String (indexed),
  "uploader_id": String,
  "content_type": String,
  "size": Number,
  "file_hash": String (SHA-256, unique),
  "upload_timestamp": DateTime,
  "is_verified": Boolean,
  "stego_analysis": {
    "file_entropy": Number,
    "is_suspicious": Boolean,
    "threat_level": String,
    "lsb_analysis": Object?,
    "metadata_analysis": Object?
  }
}
```

### Redis Keys

```
session:{session_id} → Session JSON (TTL: 3600s)
room:users:{room_id} → Hash of users
user:device:{fingerprint} → room_id (TTL: 3600s)
rate:{ip_address} → Counter (TTL: 60s)
```

## 🔄 Flujo Completo de Uso

### 1. Administrador Crea Sala
```
1. POST /api/auth/login
   → {access_token, refresh_token}
   
2. POST /api/rooms
   Headers: Authorization: Bearer {token}
   Body: {name, room_type, pin, ...}
   → {room_id, ...}
   
3. Admin comparte room_id con usuarios
```

### 2. Usuario se Une a Sala
```
1. POST /api/rooms/join
   Body: {room_id, pin, nickname}
   → {session_id, room_details}
   
2. WebSocket connect
   ws://localhost:8000/socket.io/
   
3. emit('join_room_ws')
   → Servidor agrega a sala
   → Broadcast 'user_joined'
   
4. on('room_users')
   → Recibe lista de usuarios
```

### 3. Envío de Mensaje
```
1. emit('send_message', {content, ...})
   
2. Backend:
   - Encripta mensaje (AES-256)
   - Firma mensaje (HMAC)
   - Guarda en MongoDB
   - Broadcast a sala
   
3. on('new_message')
   → Cliente muestra mensaje
```

### 4. Subida de Archivo (Multimedia)
```
1. POST /api/rooms/{id}/upload
   Body: FormData(file)
   
2. Backend (en thread separado):
   - Valida tipo y tamaño
   - Análisis de esteganografía
     * Calcula entropía
     * Análisis LSB
     * Test chi-cuadrado
     * Metadatos
   - Si sospechoso → Rechaza + Alerta
   - Si OK → Guarda + Notifica
   
3. WebSocket: emit('file_uploaded')
```

## 🛡️ Vectores de Ataque Mitigados

| Ataque | Mitigación |
|--------|-----------|
| **SQL Injection** | MongoDB (NoSQL) + Validación Pydantic |
| **XSS** | Sanitización de inputs + HTML escaping en frontend |
| **CSRF** | Tokens JWT + CORS configurado |
| **Brute Force** | Rate limiting + bcrypt (lento) |
| **Man-in-the-Middle** | TLS/SSL + Certificados |
| **Session Hijacking** | JWT firmados + Device fingerprinting |
| **Esteganografía** | Análisis multi-capa de archivos |
| **DDoS** | Rate limiting + Thread pooling |
| **Replay Attack** | Timestamps en JWT + Nonce en mensajes |
| **Data Tampering** | Firmas digitales + Hash chaining |

## 📈 Escalabilidad

### Horizontal Scaling
- **Load Balancer**: Nginx/HAProxy
- **Multiple Backend Instances**: Con Socket.IO sticky sessions
- **MongoDB Replica Set**: Para alta disponibilidad
- **Redis Cluster**: Para sesiones distribuidas

### Vertical Scaling
- **Thread Pool Size**: Ajustable según CPU cores
- **Connection Pool**: MongoDB motor con max_pool_size
- **Memory**: Redis persistencia configurable

## 🔧 Tecnologías y Versiones

| Componente | Tecnología | Versión |
|------------|-----------|---------|
| Backend Framework | FastAPI | 0.104+ |
| WebSocket | python-socketio | 5.10+ |
| Database | MongoDB | 7.0+ |
| Cache/Sessions | Redis | 7.0+ |
| Encryption | PyCryptodome | 3.19+ |
| Password Hashing | bcrypt | 4.1+ |
| JWT | python-jose | 3.3+ |
| 2FA | pyotp | 2.9+ |
| Image Processing | Pillow | 10.1+ |
| Testing | pytest | 7.4+ |
| Container | Docker | 24+ |

## 📝 Notas de Implementación

1. **Rate Limiting**: 30 requests/minuto por IP
2. **File Size**: Máximo 10MB configurable
3. **Session Timeout**: 1 hora de inactividad
4. **Token Expiry**: Access 30 min, Refresh 7 días
5. **Log Rotation**: Implementar logrotate en producción
6. **Backup Strategy**: MongoDB dump diario + logs semanales
7. **Monitoring**: Agregar Prometheus + Grafana (futuro)
8. **CI/CD**: GitHub Actions para tests automáticos (futuro)

---

**Autor**: Proyecto Integrador - ESPE  
**Fecha**: Noviembre 2025  
**Versión**: 1.0.0
