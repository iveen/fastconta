import asyncio
from app.db.base import AsyncSessionLocal, Base, engine
from app.models.global_models import Tenant, User
from app.core.security import get_password_hash
from app.core.tenant import create_tenant_schema
from sqlalchemy import select

async def create_test_data():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Tenant).where(Tenant.name == "ContaGuate"))
        tenant = result.scalar_one_or_none()
        if tenant is None:
            tenant = Tenant(
                name="ContaGuate",
                schema_name="tenant_contaguate",
                is_active=True
            )
            session.add(tenant)
            await session.flush()

            raw = "admin123"
            print("Longitud en caracteres:", len(raw))
            print("Representación repr:", repr(raw))
            print("Bytes:", len(raw.encode("utf-8")))
            hashed = get_password_hash(raw)

            user = User(
                tenant_id=tenant.id,
                email="admin@contaguate.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrador",
                role="admin",
                is_active=True
            )
            session.add(user)
            await create_tenant_schema(session, tenant.schema_name)
            await session.commit()
            print("Datos de prueba creados exitosamente.")
        else:
            print("Los datos de prueba ya existen.")

if __name__ == "__main__":
    asyncio.run(create_test_data())
