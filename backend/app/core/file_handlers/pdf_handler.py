"""
PDF Handler para FEL Guatemala.
Estrategia en 2 pasos:
  1. Intentar extraer XML embebido (adjunto o XFA).
  2. Si no hay XML, extraer texto plano con pdfplumber.
"""
import io
import logging

import pdfplumber
import pikepdf
from fastapi import UploadFile

from .base import FileContent, FileHandler, FileHandlerRegistry

logger = logging.getLogger(__name__)


@FileHandlerRegistry.register
class PdfFileHandler(FileHandler):
    SUPPORTED_EXTENSIONS = ("pdf",)
    SUPPORTED_MIMES = ("application/pdf",)

    async def read(self, upload_file: UploadFile) -> FileContent:
        raw = await upload_file.read()
        filename = upload_file.filename or "unknown.pdf"

        # Paso 1: XML embebido
        embedded_xml = self._extract_embedded_xml(raw)
        if embedded_xml:
            logger.info(f"✅ XML embebido encontrado en {filename}")
            return FileContent(
                raw_bytes=raw,
                filename=filename,
                mime_type="application/pdf",
                extension="pdf",
                parsed_data={"xml_text": embedded_xml, "source": "embedded"},
            )

        # Paso 2: Texto plano (sin OCR por ahora)
        text = self._extract_text(raw)
        logger.info(f"⚠️ PDF sin XML embebido: {filename}, extrayendo texto plano")
        return FileContent(
            raw_bytes=raw,
            filename=filename,
            mime_type="application/pdf",
            extension="pdf",
            parsed_data={"text": text, "source": "text"},
        )

    def _extract_embedded_xml(self, pdf_bytes: bytes) -> str | None:
        """Busca XML FEL embebido como adjunto (EmbeddedFile) o XFA."""
        try:
            pdf = pikepdf.open(io.BytesIO(pdf_bytes))
        except Exception as e:
            logger.warning(f"No se pudo abrir PDF con pikepdf: {e}")
            return None

        # A) Adjuntos (EmbeddedFiles)
        try:
            names = pdf.Root.get("/Names")
            if names:
                embedded = names.get("/EmbeddedFiles")
                if embedded:
                    for name_entry in embedded.get("/Names", []):
                        if isinstance(name_entry, pikepdf.String):
                            continue
                        fs = name_entry.get("/EF")
                        if fs:
                            for stream in fs.values():
                                data = stream.read_bytes()
                                if b"<dte:DTE" in data or b"GTDocumento" in data:
                                    return data.decode("utf-8", errors="replace")
        except Exception as e:
            logger.debug(f"No se encontraron adjuntos: {e}")

        # B) XFA forms
        try:
            acroform = pdf.Root.AcroForm
            if acroform and "/XFA" in acroform:
                xfa = acroform.XFA
                xml_blob = b"".join(
                    xfa[i].read_bytes() for i in range(1, len(xfa), 2)
                )
                if b"<dte:DTE" in xml_blob or b"GTDocumento" in xml_blob:
                    return xml_blob.decode("utf-8", errors="replace")
        except Exception as e:
            logger.debug(f"No hay XFA: {e}")

        return None

    def _extract_text(self, pdf_bytes: bytes) -> str:
        """Extracción de texto plano con pdfplumber."""
        chunks = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                chunks.append(t)
        return "\n".join(chunks)