# tests/test_inventario_items.py
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_crear_item_sin_autenticacion(client):
    """POST /inventarios/items/tomas/{toma_public_id} requiere autenticación"""
    toma_id = str(uuid4())
    payload = {
        "codigo": "PROD-001",
        "descripcion": "Producto de prueba",
        "cantidad": 10.0,
        "costo_unitario": 100.00,
        "bodega_codigo": "BOD-01"
    }
    response = await client.post(f"/api/v1/inventarios/items/tomas/{toma_id}", json=payload)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_crear_item_campos_faltantes(client):
    """POST /inventarios/items/tomas/{toma_public_id} valida campos obligatorios"""
    toma_id = str(uuid4())
    payload = {
        "codigo": "PROD-001"
        # Faltan: descripcion, cantidad, costo_unitario
    }
    response = await client.post(f"/api/v1/inventarios/items/tomas/{toma_id}", json=payload)
    assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
async def test_listar_items_sin_autenticacion(client):
    """GET /inventarios/items/tomas/{toma_public_id} requiere autenticación"""
    toma_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/items/tomas/{toma_id}")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_obtener_item_sin_autenticacion(client):
    """GET /inventarios/items/{public_id} requiere autenticación"""
    item_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/items/{item_id}")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_actualizar_item_sin_autenticacion(client):
    """PUT /inventarios/items/{public_id} requiere autenticación"""
    item_id = str(uuid4())
    payload = {"cantidad": 20.0}
    response = await client.put(f"/api/v1/inventarios/items/{item_id}", json=payload)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_eliminar_item_sin_autenticacion(client):
    """DELETE /inventarios/items/{public_id} requiere autenticación"""
    item_id = str(uuid4())
    response = await client.delete(f"/api/v1/inventarios/items/{item_id}")
    assert response.status_code in [401, 403]