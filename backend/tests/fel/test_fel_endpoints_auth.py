"""
Tests de integración: Verificación de autenticación en endpoints FEL.
Valida que todos los endpoints requieren autenticación.
"""
import pytest


@pytest.mark.asyncio(loop_scope="session")
async def test_upload_fel_sin_autenticacion(client):
    """POST /facturas/upload requiere autenticación."""
    files = {"files": ("test.zip", b"fake", "application/zip")}
    response = await client.post("/api/v1/facturas/upload", files=files)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_list_jobs_sin_autenticacion(client):
    """GET /facturas/jobs requiere autenticación."""
    response = await client.get("/api/v1/facturas/jobs")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_get_job_status_sin_autenticacion(client):
    """GET /facturas/jobs/{job_id} requiere autenticación."""
    job_id = 99999
    response = await client.get(f"/api/v1/facturas/jobs/{job_id}")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_cancel_job_sin_autenticacion(client):
    """POST /facturas/jobs/{job_id}/cancelar requiere autenticación."""
    job_id = 99999
    response = await client.post(f"/api/v1/facturas/jobs/{job_id}/cancelar")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio(loop_scope="session")
async def test_reprocess_job_sin_autenticacion(client):
    """POST /facturas/jobs/{job_id}/reprocesar requiere autenticación."""
    job_id = 99999
    response = await client.post(f"/api/v1/facturas/jobs/{job_id}/reprocesar")
    assert response.status_code in [401, 403]