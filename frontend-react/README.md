# Frontend React - Chat Seguro ESPE

Frontend moderno construido con React.js para el proyecto de Chat Seguro.

## 🚀 Características

- **React 18.2.0**: Framework moderno de UI
- **Socket.io-client 4.5.4**: Comunicación en tiempo real
- **crypto-js 4.2.0**: Encriptación AES256 del lado del cliente
- **React Router 6**: Navegación entre páginas
- **Axios**: Cliente HTTP para API REST

## 📋 Requisitos

- Node.js 18+ 
- npm 8+

## 🛠️ Instalación Local

```bash
cd frontend-react
npm install
```

## 🏃 Ejecución en Desarrollo

```bash
npm start
```

La aplicación se abrirá en [http://localhost:3000](http://localhost:3000)

## 🐳 Ejecución con Docker

### Opción 1: Docker Compose (Recomendado)

Desde el directorio raíz del proyecto:

```bash
# Construir y levantar todos los servicios
docker-compose up -d

# Ver logs del frontend
docker-compose logs -f frontend

# Reconstruir solo el frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

### Opción 2: Docker standalone

```bash
cd frontend-react

# Construir imagen
docker build -t securechat-frontend .

# Ejecutar contenedor
docker run -d -p 3000:80 --name frontend securechat-frontend
```

## 📁 Estructura del Proyecto

```
frontend-react/
├── public/
│   └── index.html          # HTML base
├── src/
│   ├── pages/
│   │   ├── JoinRoom.js     # Página de inicio (unirse a salas)
│   │   ├── AdminLogin.js   # Login de administrador
│   │   ├── AdminDashboard.js  # Panel de gestión de salas
│   │   └── ChatRoom.js     # Sala de chat principal
│   ├── services/
│   │   ├── api.js          # Cliente API REST
│   │   ├── crypto.js       # Encriptación AES256
│   │   └── socket.js       # Cliente Socket.IO
│   ├── App.js              # Componente raíz con rutas
│   └── index.js            # Punto de entrada
├── .env                    # Variables de entorno
├── package.json            # Dependencias
└── Dockerfile              # Imagen Docker (nginx)
```

## 🔐 Encriptación Cliente-Side

El frontend implementa encriptación AES-256 usando `crypto-js`:

```javascript
import { encryptMessage, decryptMessage } from './services/crypto';

// Encriptar antes de enviar
const encrypted = encryptMessage("Hola mundo");

// Desencriptar al recibir
const decrypted = decryptMessage(encrypted);
```

La clave de encriptación se deriva del `session_id` de cada usuario.

## 🌐 Rutas

- `/` - Página de inicio (unirse a salas públicas)
- `/admin` - Login de administrador
- `/dashboard` - Panel de administración (crear/eliminar salas)
- `/chat` - Sala de chat (requiere parámetros: room_id, session_id, nickname)

## 🔧 Variables de Entorno

Archivo `.env`:

```env
REACT_APP_API_URL=http://localhost:8000
```

En producción, cambiar a la URL del backend desplegado.

## 📦 Build de Producción

```bash
npm run build
```

Genera archivos optimizados en `build/` listos para servir con nginx/apache.

## 🐛 Troubleshooting

### Error: "Cannot connect to backend"

- Verificar que el backend esté corriendo en el puerto 8000
- Revisar CORS en `backend/.env` (debe incluir `http://localhost:3000`)
- Verificar `REACT_APP_API_URL` en `.env`

### Error: "Module not found"

```bash
rm -rf node_modules package-lock.json
npm install
```

### Problemas con Socket.IO

- Verificar que el backend tenga Socket.IO habilitado
- Revisar logs del navegador (F12) para errores de conexión
- Confirmar que no haya firewall bloqueando WebSocket

## 📝 Notas de Desarrollo

- **Hot Reload**: Los cambios se reflejan automáticamente en desarrollo
- **ESLint**: Configurado para detectar errores comunes
- **CSS Modular**: Cada componente tiene su propio archivo CSS
- **Docker Multi-stage**: Build optimizado con nginx para producción

## 🎓 Universidad de las Fuerzas Armadas ESPE

**Materia**: Desarrollo de Software Seguro  
**Proyecto**: P1 - Chat Seguro con Encriptación  
**Año**: 2024
