"""
PDF Handler para FEL Guatemala.
Estrategia en 3 pasos:
  1. Intentar extraer XML embebido (adjunto o XFA).
  2. Si no hay XML, extraer texto plano con pdfplumber.
  3. Si pdfplumber falla, usar Tesseract OCR.
"""
import io
import logging

import pdfplumber
import pikepdf
from fastapi import UploadFile

try:
    import pytesseract
    from PIL import Image
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False
    pytesseract = None

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

        # Paso 2: Texto plano con pdfplumber
        text = self._extract_text(raw)
        if text and len(text) > 100:
            logger.info(f"📄 Texto extraído con pdfplumber: {len(text)} caracteres")
            return FileContent(
                raw_bytes=raw,
                filename=filename,
                mime_type="application/pdf",
                extension="pdf",
                parsed_data={"text": text, "source": "text", "method": "pdfplumber"},
            )

        # Paso 3: Fallback a Tesseract OCR (si está disponible)
        if HAS_TESSERACT:
            logger.warning("⚠️ pdfplumber no extrajo suficiente texto, intentando OCR...")
            ocr_text = self._extract_text_ocr(raw)
            if ocr_text and len(ocr_text) > 100:
                logger.info(f"🔍 Texto extraído con Tesseract OCR: {len(ocr_text)} caracteres")
                return FileContent(
                    raw_bytes=raw,
                    filename=filename,
                    mime_type="application/pdf",
                    extension="pdf",
                    parsed_data={"text": ocr_text, "source": "text", "method": "ocr"},
                )

        logger.error(f"❌ No se pudo extraer texto del PDF: {filename}")
        return FileContent(
            raw_bytes=raw,
            filename=filename,
            mime_type="application/pdf",
            extension="pdf",
            parsed_data={"text": "", "source": "text", "method": "failed"},
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
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    t = page.extract_text() or ""
                    chunks.append(t)
        except Exception as e:
            logger.warning(f"Error en pdfplumber: {e}")
        
        return "\n".join(chunks)

    def _extract_text_ocr(self, pdf_bytes: bytes) -> str:
        """Extracción de texto con Tesseract OCR (fallback)."""
        if not HAS_TESSERACT:
            return ""

        try:
            import fitz  # PyMuPDF para convertir PDF a imagen
            
            text_chunks = []
            pdf_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                # Convertir página a imagen (300 DPI)
                pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                # OCR con Tesseract (español)
                text = pytesseract.image_to_string(img, lang='spa')
                text_chunks.append(text)
            
            pdf_doc.close()
            return "\n".join(text_chunks)
            
        except ImportError:
            logger.error("PyMuPDF no está instalado. Instala: pip install PyMuPDF")
            return ""
        except Exception as e:
            logger.error(f"Error en OCR: {e}")
            return ""