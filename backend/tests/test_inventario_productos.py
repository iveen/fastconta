# tests/test_inventario_productos.py
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_crear_producto_sin_autenticacion(client):
    """POST /inventarios/productos/{empresa_public_id} requiere autenticación"""
    empresa_id = str(uuid4())
    payload = {
        "codigo": "PROD-001",
        "descripcion": "Producto de prueba",
        "unidad_medida": "UND"
    }
    response = await client.post(f"/api/v1/inventarios/productos/{empresa_id}", json=payload)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_listar_productos_sin_autenticacion(client):
    """GET /inventarios/productos/{empresa_public_id} requiere autenticación"""
    empresa_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/productos/{empresa_id}")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_listar_productos_con_busqueda_sin_autenticacion(client):
    """GET /inventarios/productos/{empresa_public_id}?search=... requiere autenticación"""
    empresa_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/productos/{empresa_id}?search=test")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_obtener_producto_sin_autenticacion(client):
    """GET /inventarios/productos/detalle/{public_id} requiere autenticación"""
    producto_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/productos/detalle/{producto_id}")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_actualizar_producto_sin_autenticacion(client):
    """PUT /inventarios/productos/{public_id} requiere autenticación"""
    producto_id = str(uuid4())
    payload = {"descripcion": "Nueva descripción"}
    response = await client.put(f"/api/v1/inventarios/productos/{producto_id}", json=payload)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_eliminar_producto_sin_autenticacion(client):
    """DELETE /inventarios/productos/{public_id} requiere autenticación"""
    producto_id = str(uuid4())
    response = await client.delete(f"/api/v1/inventarios/productos/{producto_id}")
    assert response.status_code in [401, 403]