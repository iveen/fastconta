"""Handler ABC para lectura de archivos. No sabe de dominio."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from fastapi import UploadFile


@dataclass
class FileContent:
    """Contenedor universal del contenido leído."""
    raw_bytes: bytes
    filename: str
    mime_type: str
    extension: str
    parsed_data: Any = None


class FileHandler(ABC):
    """Interfaz base para handlers de archivos."""

    SUPPORTED_EXTENSIONS: tuple[str, ...] = ()
    SUPPORTED_MIMES: tuple[str, ...] = ()

    @abstractmethod
    async def read(self, upload_file: UploadFile) -> FileContent:
        ...

    @classmethod
    def supports(cls, filename: str, mime_type: str | None = None) -> bool:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext in cls.SUPPORTED_EXTENSIONS:
            return True
        if mime_type and mime_type in cls.SUPPORTED_MIMES:
            return True
        return False


class FileHandlerRegistry:
    """Registra y resuelve handlers por extensión/MIME."""

    _handlers: list[type[FileHandler]] = []

    @classmethod
    def register(cls, handler_cls: type[FileHandler]) -> type[FileHandler]:
        cls._handlers.append(handler_cls)
        return handler_cls

    @classmethod
    def resolve(cls, filename: str, mime_type: str | None = None) -> FileHandler:
        for handler_cls in cls._handlers:
            if handler_cls.supports(filename, mime_type):
                return handler_cls()
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "?"
        raise ValueError(f"No hay handler registrado para extensión .{ext}")