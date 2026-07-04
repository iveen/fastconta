from app.core.file_handlers import FileContent

from .strategies.base import FelIngestionStrategy, FelParsedResult
from .strategies.xml_strategy import XmlFelStrategy


class FelIngestionContext:
    STRATEGIES: list[type[FelIngestionStrategy]] = [
        XmlFelStrategy,
    ]

    @classmethod
    async def ingest(cls, content: FileContent, db) -> FelParsedResult:
        for strategy_cls in cls.STRATEGIES:
            if strategy_cls.handles(content):
                strategy = strategy_cls()
                return await strategy.parse(content, db)
        return FelParsedResult(
            success=False,
            error=f"No hay estrategia FEL para extensión .{content.extension}",
        )