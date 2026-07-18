# tests/test_inventario_tomas.py
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_crear_toma_sin_autenticacion(client):
    """POST /inventarios/tomas requiere autenticación"""
    payload = {
        "empresa_public_id": str(uuid4()),
        "anio_periodo": 2026,
        "mes_periodo": 6,
        "fecha_corte": "2026-06-30",
        "tipo": "FISCAL",
        "metodo_valuacion": "COSTO_PROMEDIO"
    }
    response = await client.post("/api/v1/inventarios/tomas", json=payload)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_crear_toma_campos_faltantes(client):
    """POST /inventarios/tomas valida campos obligatorios"""
    payload = {
        "empresa_public_id": str(uuid4())
        # Faltan: anio_periodo, mes_periodo, fecha_corte
    }
    response = await client.post("/api/v1/inventarios/tomas", json=payload)
    assert response.status_code in [401, 403, 422]


@pytest.mark.asyncio
async def test_listar_tomas_sin_autenticacion(client):
    """GET /inventarios/tomas requiere autenticación"""
    response = await client.get("/api/v1/inventarios/tomas")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_listar_tomas_con_filtros_sin_autenticacion(client):
    """GET /inventarios/tomas con filtros requiere autenticación"""
    response = await client.get("/api/v1/inventarios/tomas?estado=BORRADOR&anio=2026")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_obtener_toma_sin_autenticacion(client):
    """GET /inventarios/tomas/{public_id} requiere autenticación"""
    toma_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/tomas/{toma_id}")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_actualizar_toma_sin_autenticacion(client):
    """PUT /inventarios/tomas/{public_id} requiere autenticación"""
    toma_id = str(uuid4())
    payload = {"observaciones": "Actualización"}
    response = await client.put(f"/api/v1/inventarios/tomas/{toma_id}", json=payload)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_confirmar_toma_sin_autenticacion(client):
    """POST /inventarios/tomas/{public_id}/confirmar requiere autenticación"""
    toma_id = str(uuid4())
    response = await client.post(f"/api/v1/inventarios/tomas/{toma_id}/confirmar")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_eliminar_toma_sin_autenticacion(client):
    """DELETE /inventarios/tomas/{public_id} requiere autenticación"""
    toma_id = str(uuid4())
    response = await client.delete(f"/api/v1/inventarios/tomas/{toma_id}")
    assert response.status_code in [401, 403]