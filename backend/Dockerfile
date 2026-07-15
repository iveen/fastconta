# app/backend/Dockerfile
FROM python:3.12-slim

# Prevenir archivos .pyc y forzar salida sin buffer (crucial para ver logs en Docker)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema. 
# libpq-dev es para PostgreSQL. libcairo2-dev solo si generas PDFs.
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    pkg-config \
    libcairo2-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero para aprovechar la cache de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear usuario no-root por seguridad
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# En producción, usaremos Gunicorn con Uvicorn workers para mejor manejo de concurrencia
# Si prefieres solo Uvicorn, puedes dejar el CMD que tenías.
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2", "--limit-concurrency", "100"]