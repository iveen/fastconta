from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_next_poliza(db: AsyncSession, empresa_id: UUID, schema_name: str = None) -> str:
    """
    Obtiene el siguiente número de póliza para una empresa.
    Si no existe una secuencia, la crea con contador=1.
    """
    if not schema_name:
        raise HTTPException(status_code=500, detail="Nombre de esquema inválido")
    # 1. Buscar secuencia existente con SQL cualificado
    result = await db.execute(
        text(f"SELECT id, contador FROM {schema_name}.secuencias WHERE entidad = 'partida' AND empresa_id = :emp_id FOR UPDATE"),
        {"emp_id": empresa_id}
    )
    row = result.fetchone()

    if not row:
        # 2. Crear secuencia inicial
        await db.execute(
            text(f"INSERT INTO {schema_name}.secuencias (id, entidad, empresa_id, contador) VALUES (gen_random_uuid(), 'partida', :emp_id, 1)"),
            {"emp_id": empresa_id}
        )
        numero = 1
    else:
        secuencia_id, contador = row
        numero = contador + 1
        await db.execute(
            text(f"UPDATE {schema_name}.secuencias SET contador = :contador WHERE id = :id"),
            {"contador": numero, "id": secuencia_id}
        )

    return f"POL-{numero:04d}"