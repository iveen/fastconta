"""
Estrategia FEL para PDFs.
- Si tiene XML embebido → reutiliza parse_fel_xml (100% preciso)
- Si solo tiene texto → usa parse_fel_texto (regex)
"""
import logging

from app.core.file_handlers import FileContent
from app.services.facturas.parser_xml_service import parse_fel_xml
from app.services.fel.strategies.pdf_text_parser import parse_fel_texto

from .base import FelIngestionStrategy, FelParsedResult

logger = logging.getLogger(__name__)


class PdfFelStrategy(FelIngestionStrategy):

    @classmethod
    def handles(cls, content: FileContent) -> bool:
        return content.extension == "pdf"

    async def parse(self, content: FileContent, db) -> FelParsedResult:
        source = content.parsed_data.get("source")

        # Caso A: XML embebido → delegar al parser XML (mismo camino que XML puro)
        if source == "embedded":
            xml_text = content.parsed_data["xml_text"]
            data = await parse_fel_xml(xml_text, db)
            if not data:
                return FelParsedResult(
                    success=False,
                    error="XML embebido en PDF no es válido",
                    source_format="pdf_embedded",
                )
            return FelParsedResult(
                success=True,
                data=data,
                source_format="pdf_embedded",
            )

        # Caso B: Solo texto → intentar parsear con regex
        text = content.parsed_data.get("text", "")
        if not text or len(text) < 100:
            return FelParsedResult(
                success=False,
                error="PDF sin contenido legible",
                source_format="pdf_text",
                requires_manual_review=True,
            )

        data = await parse_fel_texto(text)
        if not data:
            return FelParsedResult(
                success=False,
                error="No se pudo extraer datos del PDF. Formato no reconocido.",
                source_format="pdf_text",
                requires_manual_review=True,
            )

        # Éxito pero marcar para revisión (los datos vienen de regex, no son 100% confiables)
        return FelParsedResult(
            success=True,
            data=data,
            source_format="pdf_text",
            requires_manual_review=True,  # ⚠️ IMPORTANTE: siempre requiere revisión
        )