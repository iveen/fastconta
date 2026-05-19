import asyncio
import sys
import uuid
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, select
from app.config import settings
from app.models.tenant_models import PeriodoFiscal
from datetime import date

async def seed(schema_name: str, empresa_id: uuid.UUID):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await session.execute(text(f"SET search_path TO {schema_name}, public"))

        result = await session.execute(
            select(PeriodoFiscal).where(PeriodoFiscal.nombre == "2026", PeriodoFiscal.empresa_id == empresa_id)
        )
        if result.scalar_one_or_none():
            print(f"El período 2026 ya existe en {schema_name} para la empresa {empresa_id}.")
            return

        periodo = PeriodoFiscal(
            nombre="2026",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
            cerrado=False,
            empresa_id=empresa_id
        )
        session.add(periodo)
        await session.commit()
        print(f"Período fiscal 2026 insertado en {schema_name} (empresa {empresa_id}).")

    await engine.dispose()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python seed_periodo_fiscal.py <tenant_schema> <empresa_id>")
        sys.exit(1)
    asyncio.run(seed(sys.argv[1], uuid.UUID(sys.argv[2])))