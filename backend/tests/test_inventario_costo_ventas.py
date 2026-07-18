# tests/test_inventario_costo_ventas.py
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_calcular_costo_ventas_sin_autenticacion(client):
    """GET /inventarios/costo-ventas/tomas/{toma_public_id} requiere autenticación"""
    toma_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/costo-ventas/tomas/{toma_id}")
    assert response.status_code in [401, 403]