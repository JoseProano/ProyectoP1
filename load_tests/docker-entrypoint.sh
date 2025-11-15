#!/bin/bash
set -e

echo "🔄 Esperando a que el backend esté disponible..."

# Esperar a que el backend esté listo
for i in {1..30}; do
    if curl -s http://securechat_backend:8000/api/health > /dev/null 2>&1; then
        echo "✅ Backend disponible"
        break
    fi
    echo "⏳ Esperando backend... ($i/30)"
    sleep 3
done

# Configurar sala automáticamente
echo ""
echo "🏗️  Configurando sala de pruebas..."
python3 /loadtests/auto_setup.py

echo ""
echo "======================================================================="
echo "  🚀 LOCUST WEB UI INICIADO"
echo "======================================================================="
echo ""
echo "📊 Abre tu navegador en: http://localhost:8089"
echo ""
echo "⚙️  Configuración sugerida:"
echo "   - Number of users: 50-100"
echo "   - Spawn rate: 10"
echo "   - Host: http://securechat_backend:8000"
echo ""
echo "======================================================================="
echo ""

# Función de limpieza al terminar
cleanup() {
    echo ""
    echo "🛑 Locust detenido - Ejecutando limpieza..."
    python3 /loadtests/cleanup.py
    exit 0
}

# Capturar señales de terminación
trap cleanup SIGTERM SIGINT

# Iniciar Locust en modo web
locust -f /loadtests/locustfile.py --host=http://securechat_backend:8000 --web-host=0.0.0.0 &

# Esperar a que termine
wait $!
