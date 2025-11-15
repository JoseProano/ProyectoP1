FROM python:3.11-slim

WORKDIR /loadtests

# Instalar curl para health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copiar archivos de prueba
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY locustfile.py .
COPY quick_test.py .
COPY setup_room.py .
COPY run_loadtest.py .
COPY auto_setup.py .
COPY cleanup.py .

# Puerto para Locust Web UI
EXPOSE 8089

# Script de inicio que espera al backend y luego inicia Locust
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["/loadtests/docker-entrypoint.sh"]
