from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.tenant_models import Secuencia

async def get_next_poliza(db: AsyncSession, empresa_id: UUID) -> str:
    """
    Obtiene el siguiente número de póliza para una empresa.
    Si no existe una secuencia, la crea con contador=1.
    """
    # Buscar secuencia existente
    stmt = select(Secuencia).where(
        Secuencia.entidad == 'partida',
        Secuencia.empresa_id == empresa_id
    ).with_for_update()  # bloquea la fila para evitar concurrencia

    result = await db.execute(stmt)
    secuencia = result.scalar_one_or_none()

    if not secuencia:
        # Crear secuencia inicial
        secuencia = Secuencia(entidad='partida', empresa_id=empresa_id, contador=1)
        db.add(secuencia)
        await db.flush()
        numero = 1
    else:
        # Incrementar contador
        secuencia.contador += 1
        numero = secuencia.contador

    # Formatear como POL-0001, POL-0002, etc.
    return f"POL-{numero:04d}"