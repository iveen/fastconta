"""
Tests unitarios de ZipFelStrategy.
Valida el parseo agregado de múltiples XMLs desde un ZIP.
"""
from unittest.mock import MagicMock

import pytest
from app.core.file_handlers import FileContent
from app.services.fel.strategies.base import FelParsedResult
from app.services.fel.strategies.zip_strategy import ZipFelStrategy


@pytest.fixture
def zip_strategy():
    """Instancia de ZipFelStrategy."""
    return ZipFelStrategy()


@pytest.fixture
def mock_db():
    """Mock de sesión de BD."""
    return MagicMock()


@pytest.fixture
def sample_xml_files():
    """Lista de XMLs de muestra (simulando salida de ZipFileHandler)."""
    return [
        {
            "filename": "factura_001.xml",
            "xml_text": '<?xml version="1.0"?><dte:DTE><uuid>ABC123</uuid></dte:DTE>',
            "raw_bytes": b'<dte:DTE><uuid>ABC123</uuid></dte:DTE>',
        },
        {
            "filename": "factura_002.xml",
            "xml_text": '<?xml version="1.0"?><dte:DTE><uuid>DEF456</uuid></dte:DTE>',
            "raw_bytes": b'<dte:DTE><uuid>DEF456</uuid></dte:DTE>',
        },
    ]


@pytest.fixture
def file_content_with_xmls(sample_xml_files):
    """FileContent simulando salida de ZipFileHandler."""
    return FileContent(
        raw_bytes=b"ZIP_BYTES",
        filename="facturas.zip",
        mime_type="application/zip",
        extension="zip",
        parsed_data={"xml_files": sample_xml_files},
    )


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_strategy_handles_zip_content(zip_strategy, file_content_with_xmls):
    """ZipFelStrategy debe detectar contenido ZIP."""
    assert zip_strategy.handles(file_content_with_xmls) is True


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_strategy_rejects_non_zip(zip_strategy):
    """ZipFelStrategy debe rechazar contenido no-ZIP."""
    xml_content = FileContent(
        raw_bytes=b"<xml/>",
        filename="test.xml",
        mime_type="application/xml",
        extension="xml",
        parsed_data={"xml_text": "<xml/>"},
    )
    assert zip_strategy.handles(xml_content) is False


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_strategy_empty_zip(zip_strategy, mock_db):
    """ZipFelStrategy debe fallar con ZIP sin XMLs."""
    empty_content = FileContent(
        raw_bytes=b"ZIP_BYTES",
        filename="empty.zip",
        mime_type="application/zip",
        extension="zip",
        parsed_data={"xml_files": []},
    )
    
    result = await zip_strategy.parse(empty_content, mock_db)
    
    assert result.success is False
    assert "no contiene archivos XML" in result.error
    assert result.source_format == "zip"


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_strategy_parses_all_xmls(zip_strategy, file_content_with_xmls, mock_db, monkeypatch):
    """ZipFelStrategy debe parsear cada XML individualmente."""
    # Mock de XmlFelStrategy para evitar parseo real
    from app.services.fel.strategies import xml_strategy
    
    async def mock_parse(self, content, db):
        return FelParsedResult(
            success=True,
            data={"numero_autorizacion": "TEST_UUID", "total": 1000.0},
            source_format="xml",
        )
    
    monkeypatch.setattr(xml_strategy.XmlFelStrategy, "parse", mock_parse)
    
    result = await zip_strategy.parse(file_content_with_xmls, mock_db)
    
    assert result.success is True
    assert result.source_format == "zip"
    assert result.data["total_files"] == 2
    assert result.data["exitos"] == 2
    assert len(result.data["parsed_results"]) == 2
    
    # Verificar que cada resultado tiene la estructura esperada
    for parsed in result.data["parsed_results"]:
        assert "filename" in parsed
        assert "success" in parsed
        assert parsed["success"] is True
        assert "data" in parsed


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_strategy_handles_partial_failures(zip_strategy, file_content_with_xmls, mock_db, monkeypatch):
    """ZipFelStrategy debe manejar fallos individuales sin detener el proceso."""
    from app.services.fel.strategies import xml_strategy
    
    call_count = 0
    
    async def mock_parse(self, content, db):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Primer XML: éxito
            return FelParsedResult(
                success=True,
                data={"numero_autorizacion": "UUID_1"},
                source_format="xml",
            )
        else:
            # Segundo XML: fallo
            return FelParsedResult(
                success=False,
                error="XML inválido",
                source_format="xml",
            )
    
    monkeypatch.setattr(xml_strategy.XmlFelStrategy, "parse", mock_parse)
    
    result = await zip_strategy.parse(file_content_with_xmls, mock_db)
    
    # Debe tener éxito parcial
    assert result.success is True  # Al menos 1 éxito
    assert result.data["exitos"] == 1
    assert len(result.data["errores"]) == 1
    assert result.data["errores"][0]["filename"] == "factura_002.xml"


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_strategy_all_failures(zip_strategy, file_content_with_xmls, mock_db, monkeypatch):
    """ZipFelStrategy debe fallar si todos los XMLs fallan."""
    from app.services.fel.strategies import xml_strategy
    
    async def mock_parse(self, content, db):
        return FelParsedResult(
            success=False,
            error="XML inválido",
            source_format="xml",
        )
    
    monkeypatch.setattr(xml_strategy.XmlFelStrategy, "parse", mock_parse)
    
    result = await zip_strategy.parse(file_content_with_xmls, mock_db)
    
    assert result.success is False
    assert result.data["exitos"] == 0
    assert len(result.data["errores"]) == 2