from fastapi import UploadFile

from .base import FileContent, FileHandler, FileHandlerRegistry


@FileHandlerRegistry.register
class XmlFileHandler(FileHandler):
    SUPPORTED_EXTENSIONS = ("xml",)
    SUPPORTED_MIMES = ("application/xml", "text/xml")

    async def read(self, upload_file: UploadFile) -> FileContent:
        raw = await upload_file.read()
        encoding = "utf-8"
        head = raw[:100].decode("utf-8", errors="ignore").lower()
        if 'encoding="' in head:
            encoding = head.split('encoding="')[1].split('"')[0]
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            text = raw.decode("utf-8", errors="replace")

        return FileContent(
            raw_bytes=raw,
            filename=upload_file.filename or "unknown.xml",
            mime_type="application/xml",
            extension="xml",
            parsed_data={"xml_text": text},
        )