# backend/tests/conftest.py
import asyncio

import pytest
from app.db.session import get_db, get_public_db
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# ✅ CORREGIDO: Usar el usuario 'fastconta_user' y tu contraseña real
# Reemplaza 'tu_password_real' por la contraseña que tiene este usuario en tu Postgres local
TEST_DATABASE_URL = "postgresql+asyncpg://fastconta_user:FF35Rv90:VHf-2U((UIh@192.168.64.4:5432/fastconta_test"

# Crear motor de base de datos de prueba
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop():
    """Crea un loop de eventos para toda la sesión de tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def db_session():
    """Crea una nueva sesión de base de datos para cada test."""
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture(scope="function")
async def client(db_session):
    """
    Cliente HTTP asíncrono para probar los endpoints.
    Sobrescribe las dependencias de base de datos para usar la de prueba.
    """
    # 1. Sobrescribir dependencias de FastAPI
    async def override_get_db():
        yield db_session

    async def override_get_public_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_public_db] = override_get_public_db

    # 2. Crear cliente de prueba usando ASGITransport
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # 3. Limpiar overrides después del test
    app.dependency_overrides.clear()