from app.core.file_handlers import FileContent
from app.services.facturas.parser_xml_service import parse_fel_xml

from .base import FelIngestionStrategy, FelParsedResult


class XmlFelStrategy(FelIngestionStrategy):

    @classmethod
    def handles(cls, content: FileContent) -> bool:
        return content.extension == "xml" or (
            content.parsed_data and "xml_text" in content.parsed_data
        )

    async def parse(self, content: FileContent, db) -> FelParsedResult:
        xml_text = content.parsed_data.get("xml_text")
        if not xml_text:
            xml_text = content.raw_bytes.decode("utf-8", errors="replace")

        data = await parse_fel_xml(xml_text, db)
        if not data:
            return FelParsedResult(
                success=False, error="XML no cumple estructura FEL",
                source_format="xml",
            )
        return FelParsedResult(success=True, data=data, source_format="xml")