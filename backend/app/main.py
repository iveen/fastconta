# backend/app/main.py
import logging
import time

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.v1.router import api_router

# 1. Configurar el formato global de los logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 2. Crear una instancia del logger para tu app
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="FastConta API", version="1.0.0")


# 3. ✅ Middleware ASGI PURO (reemplaza a @app.middleware("http"))
class LoggingMiddleware:
    """
    Middleware de logging en ASGI puro.
    Evita el bug de BaseHTTPMiddleware con pytest-asyncio
    y es más eficiente que la versión decoradora.
    """
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # Solo procesar peticiones HTTP (ignorar websocket, lifespan, etc.)
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        status_code = 500
        path = scope.get("path", "")
        method = scope.get("method", "")

        # Wrapper para capturar el status code de la respuesta
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            process_time = time.time() - start_time
            logger.info(
                f"Método: {method} | Ruta: {path} | "
                f"Estado: {status_code} | Tiempo: {process_time:.4f}s"
            )


# Registrar el middleware ASGI puro
app.add_middleware(LoggingMiddleware)


# CORS (ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir rutas
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)