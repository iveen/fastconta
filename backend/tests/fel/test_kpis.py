"""
Tests unitarios del servicio de KPIs FEL.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.services.fel.kpis_service import FELKPIsService


@pytest.mark.asyncio(loop_scope="session")
async def test_calcular_financieros_con_datos():
    """Debe calcular correctamente los KPIs financieros."""
    db = AsyncMock()
    
    # ✅ Mock con atributos nombrados (como Row de SQLAlchemy)
    mock_row = MagicMock()
    mock_row.compras_sin_iva = Decimal("5000.00")
    mock_row.ventas_locales_sin_iva = Decimal("10000.00")
    mock_row.exportaciones_sin_iva = Decimal("2000.00")
    mock_row.credito_fiscal = Decimal("600.00")
    mock_row.debito_fiscal = Decimal("1200.00")
    mock_row.total_compras = Decimal("5600.00")
    mock_row.total_ventas = Decimal("11200.00")
    
    mock_result = MagicMock()
    mock_result.first.return_value = mock_row
    db.execute = AsyncMock(return_value=mock_result)
    
    result = await FELKPIsService._calcular_financieros(
        db=db,
        empresa_id=1,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 31),
    )
    
    assert result.compras_sin_iva == Decimal("5000.00")
    assert result.ventas_locales_sin_iva == Decimal("10000.00")
    assert result.exportaciones_sin_iva == Decimal("2000.00")
    assert result.credito_fiscal == Decimal("600.00")
    assert result.debito_fiscal == Decimal("1200.00")
    assert result.iva_por_pagar == Decimal("600.00")  # 1200 - 600
    assert result.total_compras == Decimal("5600.00")
    assert result.total_ventas == Decimal("11200.00")


@pytest.mark.asyncio(loop_scope="session")
async def test_calcular_financieros_sin_datos():
    """Debe retornar ceros cuando no hay datos."""
    db = AsyncMock()
    mock_result = MagicMock()
    mock_result.first.return_value = None
    db.execute = AsyncMock(return_value=mock_result)
    
    result = await FELKPIsService._calcular_financieros(
        db=db,
        empresa_id=1,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 31),
    )
    
    assert result.compras_sin_iva == Decimal("0")
    assert result.ventas_locales_sin_iva == Decimal("0")
    assert result.iva_por_pagar == Decimal("0")


@pytest.mark.asyncio(loop_scope="session")
async def test_calcular_conteos():
    """Debe contar correctamente los documentos."""
    db = AsyncMock()
    
    # ✅ Mock con atributos nombrados
    mock_row = MagicMock()
    mock_row.emitidos = 15
    mock_row.recibidos = 25
    mock_row.anulados = 3
    mock_row.total = 43
    
    mock_result = MagicMock()
    mock_result.first.return_value = mock_row
    db.execute = AsyncMock(return_value=mock_result)
    
    result = await FELKPIsService._calcular_conteos(
        db=db,
        empresa_id=1,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 1, 31),
    )
    
    assert result.emitidos == 15
    assert result.recibidos == 25
    assert result.anulados == 3
    assert result.total == 43


@pytest.mark.asyncio(loop_scope="session")
async def test_calcular_series_temporales():
    """Debe agrupar datos por mes correctamente."""
    db = AsyncMock()
    
    # ✅ Mock con atributos nombrados
    mock_row_1 = MagicMock()
    mock_row_1.periodo = "2026-01"
    mock_row_1.compras = Decimal("5000")
    mock_row_1.ventas_locales = Decimal("10000")
    mock_row_1.exportaciones = Decimal("2000")
    mock_row_1.credito_fiscal = Decimal("600")
    mock_row_1.debito_fiscal = Decimal("1200")
    mock_row_1.documentos_emitidos = 10
    mock_row_1.documentos_recibidos = 15
    
    mock_row_2 = MagicMock()
    mock_row_2.periodo = "2026-02"
    mock_row_2.compras = Decimal("6000")
    mock_row_2.ventas_locales = Decimal("12000")
    mock_row_2.exportaciones = Decimal("2500")
    mock_row_2.credito_fiscal = Decimal("720")
    mock_row_2.debito_fiscal = Decimal("1440")
    mock_row_2.documentos_emitidos = 12
    mock_row_2.documentos_recibidos = 18
    
    mock_result = MagicMock()
    mock_result.__iter__ = MagicMock(return_value=iter([mock_row_1, mock_row_2]))
    db.execute = AsyncMock(return_value=mock_result)
    
    result = await FELKPIsService._calcular_series_temporales(
        db=db,
        empresa_id=1,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 2, 28),
    )
    
    assert len(result) == 2
    assert result[0].periodo == "2026-01"
    assert result[0].compras == Decimal("5000")
    assert result[0].ventas_locales == Decimal("10000")
    assert result[0].documentos_emitidos == 10
    assert result[1].periodo == "2026-02"
    assert result[1].compras == Decimal("6000")
    assert result[1].documentos_emitidos == 12