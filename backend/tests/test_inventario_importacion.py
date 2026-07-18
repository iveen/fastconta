# tests/test_inventario_importacion.py
import io
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_importar_inventario_sin_autenticacion(client):
    """POST /inventarios/importaciones/tomas/{toma_public_id}/importar requiere autenticación"""
    toma_id = str(uuid4())
    
    # Crear archivo CSV de prueba
    csv_content = b"codigo,descripcion,cantidad,costo_unitario\nPROD-001,Producto 1,10,100.00"
    files = {"file": ("inventario.csv", io.BytesIO(csv_content), "text/csv")}
    
    response = await client.post(
        f"/api/v1/inventarios/importaciones/tomas/{toma_id}/importar?modo=REEMPLAZAR",
        files=files
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_importar_inventario_formato_invalido_sin_autenticacion(client):
    """POST /inventarios/importaciones/tomas/{toma_public_id}/importar valida formato"""
    toma_id = str(uuid4())
    
    # Archivo con formato no soportado
    files = {"file": ("inventario.txt", io.BytesIO(b"contenido"), "text/plain")}
    
    response = await client.post(
        f"/api/v1/inventarios/importaciones/tomas/{toma_id}/importar?modo=REEMPLAZAR",
        files=files
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_listar_importaciones_sin_autenticacion(client):
    """GET /inventarios/importaciones/tomas/{toma_public_id}/historial requiere autenticación"""
    toma_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/importaciones/tomas/{toma_id}/historial")
    assert response.status_code in [401, 403]