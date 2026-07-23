"""
Tests unitarios de ZipFileHandler.
Valida extracción de XMLs desde ZIPs del SAT.
"""
import io
import zipfile

import pytest
from app.core.file_handlers.zip_handler import ZipFileHandler
from fastapi import UploadFile


@pytest.fixture
def zip_handler():
    """Instancia de ZipFileHandler."""
    return ZipFileHandler()


@pytest.fixture
def sample_xml_content():
    """XML FEL de muestra (simplificado)."""
    return b"""<?xml version="1.0" encoding="UTF-8"?>
<dte:DTE xmlns:dte="http://www.sat.gob.gt/dte/fel/0.2.0">
  <dte:DatosEmision>
    <dte:Emisor>
      <dte:NITEmisor>1234567</dte:NITEmisor>
      <dte:NombreEmisor>Empresa Test S.A.</dte:NombreEmisor>
    </dte:Emisor>
    <dte:Receptor>
      <dte:NITReceptor>7654321</dte:NITReceptor>
      <dte:NombreReceptor>Cliente Test</dte:NombreReceptor>
    </dte:Receptor>
    <dte:Totales>
      <dte:Total>1000.00</dte:Total>
    </dte:Totales>
  </dte:DatosEmision>
</dte:DTE>"""


@pytest.fixture
def sample_zip_with_xmls(sample_xml_content):
    """Crea un ZIP con 2 XMLs válidos."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("factura_001.xml", sample_xml_content)
        zip_file.writestr("factura_002.xml", sample_xml_content)
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


@pytest.fixture
def sample_zip_empty():
    """Crea un ZIP sin XMLs."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("readme.txt", b"Este ZIP no contiene XMLs")
    zip_buffer.seek(0)
    return zip_buffer.getvalue()


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_handler_extracts_xmls(zip_handler, sample_zip_with_xmls):
    """ZipFileHandler debe extraer todos los XMLs del ZIP."""
    upload_file = UploadFile(
        filename="facturas_sat.zip",
        file=io.BytesIO(sample_zip_with_xmls),
    )
    
    content = await zip_handler.read(upload_file)
    
    assert content.extension == "zip"
    assert content.mime_type == "application/zip"
    assert content.parsed_data is not None
    assert "xml_files" in content.parsed_data
    assert len(content.parsed_data["xml_files"]) == 2
    
    # Verificar que cada XML tiene la estructura esperada
    for xml_data in content.parsed_data["xml_files"]:
        assert "filename" in xml_data
        assert "xml_text" in xml_data
        assert "raw_bytes" in xml_data
        assert xml_data["filename"].endswith(".xml")


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_handler_empty_zip(zip_handler, sample_zip_empty):
    """ZipFileHandler debe manejar ZIPs sin XMLs."""
    upload_file = UploadFile(
        filename="empty.zip",
        file=io.BytesIO(sample_zip_empty),
    )
    
    content = await zip_handler.read(upload_file)
    
    assert content.extension == "zip"
    assert len(content.parsed_data["xml_files"]) == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_handler_invalid_zip(zip_handler):
    """ZipFileHandler debe rechazar archivos ZIP corruptos."""
    upload_file = UploadFile(
        filename="corrupt.zip",
        file=io.BytesIO(b"This is not a valid ZIP file"),
    )
    
    with pytest.raises(ValueError, match="Archivo ZIP inválido"):
        await zip_handler.read(upload_file)


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_handler_mixed_content(zip_handler, sample_xml_content):
    """ZipFileHandler debe ignorar archivos no-XML dentro del ZIP."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("factura.xml", sample_xml_content)
        zip_file.writestr("readme.txt", b"Texto no relevante")
        zip_file.writestr("imagen.png", b"\x89PNG\r\n\x1a\n")
    zip_buffer.seek(0)
    
    upload_file = UploadFile(
        filename="mixed.zip",
        file=io.BytesIO(zip_buffer.getvalue()),
    )
    
    content = await zip_handler.read(upload_file)
    
    # Solo debe extraer el XML
    assert len(content.parsed_data["xml_files"]) == 1
    assert content.parsed_data["xml_files"][0]["filename"] == "factura.xml"


@pytest.mark.asyncio(loop_scope="session")
async def test_zip_handler_encoding_detection(zip_handler):
    """ZipFileHandler debe detectar encoding del XML."""
    xml_utf8 = b'<?xml version="1.0" encoding="UTF-8"?><root>Test</root>'
    xml_iso = b'<?xml version="1.0" encoding="ISO-8859-1"?><root>Test</root>'
    
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("utf8.xml", xml_utf8)
        zip_file.writestr("iso.xml", xml_iso)
    zip_buffer.seek(0)
    
    upload_file = UploadFile(
        filename="encodings.zip",
        file=io.BytesIO(zip_buffer.getvalue()),
    )
    
    content = await zip_handler.read(upload_file)
    
    assert len(content.parsed_data["xml_files"]) == 2
    # Ambos deben ser parseados correctamente
    for xml_data in content.parsed_data["xml_files"]:
        assert "<root>Test</root>" in xml_data["xml_text"]