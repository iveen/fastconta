from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.db.base import engine, Base

app = FastAPI(title="FastConta API", version="1.0.0")

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
'''
# Evento de inicio para crear tablas (solo desarrollo)
@app.on_event("startup")
async def startup_event():
    # Crear tablas automáticamente (solo si no se usa Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
'''