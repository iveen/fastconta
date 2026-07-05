"""
Estrategia FEL para PDFs.
- Si tiene XML embebido → reutiliza parse_fel_xml (100% preciso)
- Si solo tiene texto → marca para revisión manual (no intenta adivinar)
"""
import logging

from app.core.file_handlers import FileContent
from app.services.fel_parser import parse_fel_xml

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

        # Caso B: Solo texto → marcar para revisión manual
        # NO intentamos regex aquí porque es propenso a errores en NITs y montos
        return FelParsedResult(
            success=False,
            error="PDF sin XML embebido. Requiere revisión manual o OCR.",
            source_format="pdf_text",
            requires_manual_review=True,
        )