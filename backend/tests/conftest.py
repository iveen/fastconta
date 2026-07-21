# backend/tests/conftest.py
import asyncio
import os
from urllib.parse import quote_plus

import pytest
import pytest_asyncio
from app.db.session import get_db, get_public_db
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

try:
    from app.db.base import Base
except ImportError:
    from app.models.global_models import Base

# ============================================================
# 0. EVENT LOOP DE SESIÓN (DEBE IR PRIMERO)
# ============================================================
@pytest.fixture(scope="session")
def event_loop():
    """
    Fixture especial de pytest-asyncio.
    DEBE ser pytest.fixture (síncrono), no pytest_asyncio.fixture.
    Crea un único event loop para toda la sesión de tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# ============================================================
# 1. Configuración de BD
# ============================================================
db_host = os.getenv("DATABASE_HOST", "localhost")
db_port = os.getenv("DATABASE_PORT", "5432")
db_user = os.getenv("DATABASE_USER", "fastconta")
db_password = os.getenv("DATABASE_PASSWORD", "fastconta")
db_name = os.getenv("DATABASE_NAME", "fastconta_test")

password = quote_plus(db_password)
TEST_DATABASE_URL = f"postgresql+asyncpg://{db_user}:{password}@{db_host}:{db_port}/{db_name}"

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

# ============================================================
# 2. Cliente HTTP SESSION-SCOPED
# ============================================================
@pytest_asyncio.fixture(scope="session")
async def http_client():
    """
    AsyncClient que vive durante TODA la sesión de tests.
    Se ejecuta en el event_loop de sesión, evitando 'different loop'.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

# ============================================================
# 3. Setup de BD por test (Nuke and Pave)
# ============================================================
@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_test_db():
    """Recrea el schema public antes de cada test."""
    async with test_engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        await conn.run_sync(Base.metadata.create_all)
    yield

# ============================================================
# 4. Sesión de BD por test (conexión simple + rollback)
# ============================================================
@pytest_asyncio.fixture(scope="function")
async def db_session():
    """
    Sesión limpia para cada test.
    Usa TestSessionLocal con rollback al final (no transacciones anidadas
    porque setup_test_db ya hace DROP/CREATE del schema).
    """
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()
        await session.close()

# ============================================================
# 5. Fixture 'client' que combina http_client + db_session
# ============================================================
@pytest_asyncio.fixture(scope="function")
async def client(http_client, db_session):
    """
    Inyecta la sesión de BD del test en las dependencias de FastAPI.
    El http_client es session-scoped (mismo loop durante toda la sesión).
    Las dependencias se actualizan en cada test (aislamiento).
    """
    async def override_get_db():
        yield db_session

    async def override_get_public_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_public_db] = override_get_public_db

    yield http_client

    app.dependency_overrides.clear()