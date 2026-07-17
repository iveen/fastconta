import pytest


@pytest.mark.asyncio
async def test_create_user_sin_autenticacion(client):
    payload = {
        "full_name": "Juan Pérez",
        "email": "juan@test.com",
        "role": "tenant_member"
    }
    response = await client.post("/api/v1/users/", json=payload)
    assert response.status_code in [401, 403]

@pytest.mark.asyncio
async def test_create_user_campos_faltantes(client):
    payload = {
        "email": "juan@test.com"
    }
    response = await client.post("/api/v1/users/", json=payload)
    assert response.status_code in [401, 403, 422]