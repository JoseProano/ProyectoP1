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

#### 🔐 Encriptación End-to-End (E2E) - Cliente a Cliente
```
Cliente Emisor (Navegador)
    │
    ▼
┌────────────────────────────┐
│  Usuario escribe mensaje   │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│  Generar clave de sala     │
│  PBKDF2(room_id + PIN)     │
│  10,000 iteraciones        │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│  Encriptar con AES-256-CBC │
│  CryptoJS.AES.encrypt()    │
│  Salt aleatorio por mensaje│
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│  Resultado: U2FsdGVkX1+... │
│  (Base64 del ciphertext)   │
└──────────┬─────────────────┘
           │
           ▼
    WebSocket emit
  encrypted_content only
           │
           ▼
┌────────────────────────────┐
│  SERVIDOR (Backend)        │
│  - NO desencripta          │
│  - Almacena cipher en DB   │
│  - Transmite cipher        │
└──────────┬─────────────────┘
           │
           ▼
    WebSocket broadcast
  encrypted_content only
           │
           ▼
Cliente Receptor (Navegador)
    │
    ▼
┌────────────────────────────┐
│  Recuperar clave de sala   │
│  desde sessionStorage      │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│  Desencriptar AES-256-CBC  │
│  CryptoJS.AES.decrypt()    │
└──────────┬─────────────────┘
           │
           ▼
┌────────────────────────────┐
│  Mostrar mensaje en claro  │
└────────────────────────────┘
```

**Características de la E2E:**
- ✅ Clave derivada de `room_id + PIN` (conocida solo por usuarios con PIN)
- ✅ Servidor NUNCA ve el contenido en claro
- ✅ Resistente a compromiso del servidor (forward secrecy parcial)
- ✅ 10,000 iteraciones PBKDF2 (dificulta ataques de diccionario)
- ✅ Salt aleatorio por mensaje (evita patrones repetidos)
- ⚠️ Sin Perfect Forward Secrecy completo (usa PIN estático)
- ⚠️ Vulnerable si el PIN es débil (4-8 dígitos)

#### Otras Capas de Encriptación
```
Datos en Reposo:
├── AES-256-CBC (mensajes E2E en MongoDB - servidor no puede leer)
├── bcrypt (contraseñas, PINs - cost factor 12)
└── SHA-256 (hashes de archivos)

Datos en Tránsito:
├── TLS 1.3 (canal de transporte)
└── E2E Encryption (contenido de mensajes - adicional al TLS)
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
  "nickname": String,
  "content": String (deprecated - siempre "[Encrypted]"),
  "encrypted_content": String (E2E cipher - servidor NO puede leer),
  "encrypted": Boolean (siempre true para E2E),
  "timestamp": DateTime (indexed),
  "signature": String (HMAC del encrypted_content)
}
```

**Nota sobre E2E**: El campo `encrypted_content` contiene el resultado de `CryptoJS.AES.encrypt()` en formato Base64 (ej: `"U2FsdGVkX1+..."`). El servidor almacena este valor SIN desencriptarlo y lo transmite tal cual a los receptores. Solo los clientes con el PIN correcto pueden derivar la clave PBKDF2 y desencriptar el contenido.

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

## 📱 Arquitectura Responsive

### Sistema de Breakpoints
```
┌─────────────────────────────────────────────────────────┐
│  Desktop (> 1024px)                                     │
│  ┌──────────┬──────────┬──────────┐                    │
│  │  Header  │  Header  │  Header  │                    │
│  ├──────────┴──────────┴──────────┤                    │
│  │  Sidebar │      Main Content   │                    │
│  │          │                      │                    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Tablet (768px - 1024px)                                │
│  ┌──────────────────────────────────┐                  │
│  │          Header                  │                  │
│  ├────────────┬─────────────────────┤                  │
│  │  Sidebar   │   Main Content      │                  │
│  │ (colapsado)│                      │                  │
└─────────────────────────────────────────────────────────┘

┌──────────────────────────────┐
│  Mobile (< 768px)            │
│  ┌──────────────────────────┐│
│  │       Header             ││
│  ├──────────────────────────┤│
│  │       Sidebar            ││
│  │      (stacked)           ││
│  ├──────────────────────────┤│
│  │                          ││
│  │     Main Content         ││
│  │      (full-width)        ││
│  │                          ││
│  └──────────────────────────┘│
└──────────────────────────────┘
```

### CSS Global (App.css)
```css
* {
  box-sizing: border-box;  /* Incluye padding/border en width */
  margin: 0;
  padding: 0;
}

html, body {
  width: 100%;
  overflow-x: hidden;      /* Previene scroll horizontal */
  -webkit-overflow-scrolling: touch;  /* Smooth scroll iOS */
}
```

### Técnicas Responsive Usadas

1. **Viewport Units Dinámicos**:
   ```css
   height: 100dvh;  /* Respeta barra de navegación móvil */
   max-width: 100vw;
   ```

2. **Fuentes Fluidas con clamp()**:
   ```css
   font-size: clamp(16px, 4vw, 24px);
   /* Mínimo 16px, ideal 4% viewport, máximo 24px */
   ```

3. **Flexbox Responsive**:
   ```css
   .header {
     display: flex;
     flex-direction: row;  /* Desktop */
   }
   @media (max-width: 768px) {
     .header {
       flex-direction: column;  /* Mobile */
     }
   }
   ```

4. **Grid Adaptable**:
   ```css
   .rooms-grid {
     grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
     /* Auto-ajusta según espacio disponible */
   }
   ```

5. **Touch Targets**:
   ```css
   button {
     min-height: 44px;  /* Recomendación WCAG para touch */
     min-width: 44px;
   }
   ```

### Componentes con Responsive

| Componente | Desktop | Tablet | Mobile |
|------------|---------|--------|--------|
| **Header** | Horizontal, 2 secciones | Horizontal, wrapped | Vertical, stacked |
| **Sidebar** | 250px fijo | 200px colapsable | Full-width, max-height 200px |
| **Mensajes** | 70% ancho | 80% ancho | 85-92% ancho |
| **Botones** | Auto-size | Auto-size | Full-width |
| **Formularios** | 2 columnas | 2 columnas | 1 columna |
| **Modals** | 500px max | 90% ancho | 95% ancho |

## 📝 Notas de Implementación

1. **Rate Limiting**: 30 requests/minuto por IP (HTTP), 30 mensajes/minuto (WebSocket)
2. **File Size**: Máximo 10MB configurable
3. **Session Timeout**: 1 hora de inactividad
4. **Token Expiry**: Access 30 min, Refresh 7 días
5. **Log Rotation**: Implementar logrotate en producción
6. **Backup Strategy**: MongoDB dump diario + logs semanales
7. **Monitoring**: Agregar Prometheus + Grafana (futuro)
8. **CI/CD**: GitHub Actions para tests automáticos (futuro)
9. **E2E Encryption**: PBKDF2 con 10,000 iteraciones, AES-256-CBC
10. **Responsive**: Breakpoints 480px, 768px, 1024px con overflow control

---

**Autor**: Proyecto Integrador - ESPE  
**Fecha**: Noviembre 2025  
**Versión**: 1.0.0
