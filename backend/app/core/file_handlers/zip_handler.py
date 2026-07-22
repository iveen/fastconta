"""
ZIP Handler para FEL Guatemala.
Extrae todos los XMLs de un archivo ZIP del SAT.
"""
import io
import logging
import zipfile

from fastapi import UploadFile

from .base import FileContent, FileHandler, FileHandlerRegistry

logger = logging.getLogger(__name__)

@FileHandlerRegistry.register
class ZipFileHandler(FileHandler):
    SUPPORTED_EXTENSIONS = ("zip",)
    SUPPORTED_MIMES = ("application/zip", "application/x-zip-compressed")
    
    async def read(self, upload_file: UploadFile) -> FileContent:
        """
        Extrae todos los XMLs del ZIP y los retorna como lista.
        El endpoint detectará que es un ZIP y lo enviará a la cola.
        """
        raw = await upload_file.read()
        filename = upload_file.filename or "unknown.zip"
        
        xml_files = []
        
        try:
            with zipfile.ZipFile(io.BytesIO(raw), 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.lower().endswith('.xml'):
                        xml_bytes = zip_ref.read(file_info.filename)
                        
                        # Detectar encoding
                        encoding = "utf-8"
                        head = xml_bytes[:100].decode("utf-8", errors="ignore").lower()
                        if 'encoding="' in head:
                            encoding = head.split('encoding="')[1].split('"')[0]
                        
                        try:
                            xml_text = xml_bytes.decode(encoding)
                        except UnicodeDecodeError:
                            xml_text = xml_bytes.decode("utf-8", errors="replace")
                        
                        xml_files.append({
                            "filename": file_info.filename,
                            "xml_text": xml_text,
                            "raw_bytes": xml_bytes
                        })
                
                logger.info(f"✅ ZIP extraído: {len(xml_files)} XMLs encontrados en {filename}")
        
        except zipfile.BadZipFile as e:
            logger.error(f"❌ ZIP inválido: {filename}: {e}")
            raise ValueError(f"Archivo ZIP inválido: {e}")
        
        return FileContent(
            raw_bytes=raw,
            filename=filename,
            mime_type="application/zip",
            extension="zip",
            parsed_data={
                "xml_files": xml_files,
                "total_files": len(xml_files),
                "source": "zip"
            }
        )