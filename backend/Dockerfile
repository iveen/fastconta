# app/backend/Dockerfile
FROM python:3.12-slim

# Prevenir archivos .pyc y forzar salida sin buffer (mejor para logs de Docker)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema necesarias para psycopg2 y compilacion
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar la cache de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del codigo de la aplicacion
COPY . .

# Crear usuario no-root por seguridad (buena practica en produccion)
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Exponer puerto interno del contenedor
EXPOSE 8001

# Comando de inicio con Uvicorn (2 workers es un buen punto de partida para ARM/Oracle)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2"]