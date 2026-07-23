"""
Tests unitarios de templates de email FEL.
Valida renderizado de templates Jinja2.
"""
import pytest
from app.core.email.renderer import email_renderer


@pytest.mark.asyncio(loop_scope="session")
async def test_fel_import_completada_template():
    """Template de importación completada debe renderizar sin errores."""
    html = email_renderer.render(
        "fel_import_completada.html",
        context={
            "full_name": "Juan Pérez",
            "archivo_nombre": "facturas_sat.zip",
            "total_archivos": 10,
            "facturas_creadas": 8,
            "facturas_duplicadas": 1,
            "facturas_con_error": 1,
        },
    )
    assert "Juan Pérez" in html
    assert "facturas_sat.zip" in html
    assert "10" in html
    assert "8" in html
    assert "1" in html


@pytest.mark.asyncio(loop_scope="session")
async def test_fel_import_fallida_template():
    """Template de importación fallida debe renderizar sin errores."""
    html = email_renderer.render(
        "fel_import_fallida.html",
        context={
            "full_name": "María García",
            "archivo_nombre": "error.zip",
            "error_mensaje": "ZIP corrupto",
        },
    )
    assert "María García" in html
    assert "error.zip" in html
    assert "ZIP corrupto" in html


@pytest.mark.asyncio(loop_scope="session")
async def test_fel_import_cancelada_template():
    """Template de importación cancelada debe renderizar sin errores."""
    html = email_renderer.render(
        "fel_import_cancelada.html",
        context={
            "full_name": "Carlos López",
            "archivo_nombre": "cancelado.zip",
            "archivos_procesados": 5,
            "archivos_totales": 10,
        },
    )
    assert "Carlos López" in html
    assert "cancelado.zip" in html
    assert "5" in html
    assert "10" in html