# tests/test_inventario_bodegas.py
from uuid import uuid4

import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_crear_bodega_sin_autenticacion(client):
    """POST /inventarios/bodegas/{empresa_public_id} requiere autenticación"""
    empresa_id = str(uuid4())
    payload = {
        "codigo": "BOD-01",
        "nombre": "Bodega Central",
        "ubicacion": "Zona 10"
    }
    response = await client.post(f"/api/v1/inventarios/bodegas/{empresa_id}", json=payload)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_listar_bodegas_sin_autenticacion(client):
    """GET /inventarios/bodegas/{empresa_public_id} requiere autenticación"""
    empresa_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/bodegas/{empresa_id}")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_obtener_bodega_sin_autenticacion(client):
    """GET /inventarios/bodegas/detalle/{public_id} requiere autenticación"""
    bodega_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/bodegas/detalle/{bodega_id}")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_actualizar_bodega_sin_autenticacion(client):
    """PUT /inventarios/bodegas/{public_id} requiere autenticación"""
    bodega_id = str(uuid4())
    payload = {"nombre": "Nuevo Nombre"}
    response = await client.put(f"/api/v1/inventarios/bodegas/{bodega_id}", json=payload)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_eliminar_bodega_sin_autenticacion(client):
    """DELETE /inventarios/bodegas/{public_id} requiere autenticación"""
    bodega_id = str(uuid4())
    response = await client.delete(f"/api/v1/inventarios/bodegas/{bodega_id}")
    assert response.status_code in [401, 403]