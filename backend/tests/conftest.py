# backend/tests/conftest.py
from urllib.parse import quote_plus

import pytest_asyncio
from app.db.session import get_db, get_public_db
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

try:
    from app.db.base import Base
except ImportError:
    from app.models.global_models import Base

# Codificar la contraseña correctamente
password = quote_plus('FF35Rv90:VHf-2U((UIh')
TEST_DATABASE_URL = f"postgresql+asyncpg://fastconta_user:{password}@192.168.64.4:5432/fastconta_test"

# Engine con pool_size reducido para evitar conflictos
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=0,
    pool_pre_ping=True,
)
TestSessionLocal = sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)

# ------------------------------------------------------------
# Fixture para crear/eliminar tablas (autouse)
# ------------------------------------------------------------
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Crea las tablas antes del test y las elimina después."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    # Forzar cierre de todas las conexiones del pool
    await test_engine.dispose()

# ------------------------------------------------------------
# Fixture de sesión de BD (sin transacción anidada para evitar problemas)
# ------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provee una sesión limpia para el test. No se inicia transacción explícita."""
    async with TestSessionLocal() as session:
        yield session
        # Deshace cualquier cambio pendiente
        await session.rollback()
        await session.close()

# ------------------------------------------------------------
# Fixture cliente HTTP con sobrescritura de dependencias
# ------------------------------------------------------------
@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    """Cliente HTTP que usa la sesión de prueba."""
    # Sobrescribir dependencias para que devuelvan la misma sesión
    async def override_get_db():
        yield db_session

    async def override_get_public_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_public_db] = override_get_public_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Limpiar sobrescrituras después del test
    app.dependency_overrides.clear()