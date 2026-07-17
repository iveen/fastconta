import pytest


@pytest.mark.asyncio
async def test_listar_regimenes_activos_success(client):
    response = await client.get("/api/v1/regimenes-fiscales/activos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_listar_regimenes_fiscales_con_filtros(client):
    response = await client.get("/api/v1/regimenes-fiscales/?skip=0&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert data["skip"] == 0
    assert data["limit"] == 10