from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.db.base import engine, Base
import logging
import time
import uvicorn

# 1. Configurar el formato global de los logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 2. Crear una instancia del logger para tu app
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="FastConta API", version="1.0.0")

# 3. Crear un middleware para registrar las peticiones entrantes
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Procesar la petición y esperar la respuesta
    response = await call_next(request)
    
    process_time = time.time() - start_time
    formatted_process_time = f"{process_time:.4f}"
    
    # Registrar la información de la petición
    logger.info(
        f"Método: {request.method} | Ruta: {request.url.path} | "
        f"Estado: {response.status_code} | Tiempo: {formatted_process_time}s"
    )
    
    return response

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
'''
# Evento de inicio para crear tablas (solo desarrollo)
@app.on_event("startup")
async def startup_event():
    # Crear tablas automáticamente (solo si no se usa Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
'''