# tests/test_inventario_export.py
from uuid import uuid4

import pytest


@pytest.mark.asyncio
async def test_exportar_toma_excel_sin_autenticacion(client):
    """GET /inventarios/export/tomas/{toma_public_id}?formato=excel requiere autenticación"""
    toma_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/export/tomas/{toma_id}?formato=excel")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_exportar_toma_pdf_sin_autenticacion(client):
    """GET /inventarios/export/tomas/{toma_public_id}?formato=pdf requiere autenticación"""
    toma_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/export/tomas/{toma_id}?formato=pdf")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_exportar_toma_formato_invalido_sin_autenticacion(client):
    """GET /inventarios/export/tomas/{toma_public_id}?formato=invalid valida formato"""
    toma_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/export/tomas/{toma_id}?formato=invalid")
    assert response.status_code in [401, 403, 422]