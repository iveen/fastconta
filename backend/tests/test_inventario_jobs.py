"""
Tests para endpoints de jobs de importación de inventarios.
"""
import io
from uuid import uuid4

import pytest

# ============================================================
# ENDPOINTS DE USUARIO NORMAL
# ============================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_listar_jobs_usuario_sin_autenticacion(client):
    """GET /inventarios/importaciones/jobs requiere autenticación"""
    response = await client.get("/api/v1/inventarios/importaciones/jobs")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_consultar_estado_job_sin_autenticacion(client):
    """GET /inventarios/importaciones/jobs/{job_id} requiere autenticación"""
    job_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/importaciones/jobs/{job_id}")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_cancelar_job_sin_autenticacion(client):
    """POST /inventarios/importaciones/jobs/{job_id}/cancelar requiere autenticación"""
    job_id = str(uuid4())
    response = await client.post(f"/api/v1/inventarios/importaciones/jobs/{job_id}/cancelar")
    assert response.status_code in [401, 403]


# ============================================================
# ENDPOINTS DE IMPORTACIÓN ASÍNCRONA
# ============================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_importar_inventario_async_sin_autenticacion(client):
    """POST /inventarios/importaciones/tomas/{toma_id}/importar requiere autenticación"""
    toma_id = str(uuid4())
    
    # Simular archivo CSV
    import io
    csv_content = b"codigo,descripcion,cantidad,costo_unitario\nPROD-001,Producto 1,10,100.00"
    files = {"file": ("inventario.csv", io.BytesIO(csv_content), "text/csv")}
    
    response = await client.post(
        f"/api/v1/inventarios/importaciones/tomas/{toma_id}/importar?modo=REEMPLAZAR",
        files=files
    )
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_importar_inventario_formato_invalido_sin_autenticacion(client):
    """POST /inventarios/importaciones/tomas/{toma_id}/importar valida formato"""
    toma_id = str(uuid4())
    
    # Archivo con formato no soportado
    files = {"file": ("inventario.txt", io.BytesIO(b"contenido"), "text/plain")}
    
    response = await client.post(
        f"/api/v1/inventarios/importaciones/tomas/{toma_id}/importar?modo=REEMPLAZAR",
        files=files
    )
    assert response.status_code in [401, 403]


# ============================================================
# ENDPOINTS DE SUPERADMIN
# ============================================================


@pytest.mark.asyncio(loop_scope="session")
async def test_listar_jobs_global_sin_autenticacion(client):
    """GET /inventarios/importaciones/admin/jobs requiere autenticación"""
    response = await client.get("/api/v1/inventarios/importaciones/admin/jobs")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_estadisticas_jobs_global_sin_autenticacion(client):
    """GET /inventarios/importaciones/admin/jobs/estadisticas requiere autenticación"""
    response = await client.get("/api/v1/inventarios/importaciones/admin/jobs/estadisticas")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_consultar_job_admin_sin_autenticacion(client):
    """GET /inventarios/importaciones/admin/jobs/{job_id} requiere autenticación"""
    job_id = str(uuid4())
    response = await client.get(f"/api/v1/inventarios/importaciones/admin/jobs/{job_id}")
    assert response.status_code in [401, 403]