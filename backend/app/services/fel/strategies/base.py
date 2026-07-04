from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.core.file_handlers import FileContent


@dataclass
class FelParsedResult:
    success: bool
    data: dict = field(default_factory=dict)
    error: str | None = None
    source_format: str = ""
    requires_manual_review: bool = False


class FelIngestionStrategy(ABC):
    @abstractmethod
    async def parse(self, content: FileContent, db) -> FelParsedResult:
        ...

    @classmethod
    @abstractmethod
    def handles(cls, content: FileContent) -> bool:
        ...