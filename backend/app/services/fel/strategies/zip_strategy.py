"""
Estrategia FEL para archivos ZIP del SAT.
Extrae todos los XMLs del ZIP y los procesa individualmente usando XmlFelStrategy.
"""
import logging

from app.core.file_handlers import FileContent

from .base import FelIngestionStrategy, FelParsedResult
from .xml_strategy import XmlFelStrategy

logger = logging.getLogger(__name__)

class ZipFelStrategy(FelIngestionStrategy):
    """
    Estrategia para procesar ZIPs que contienen múltiples XMLs FEL.
    """
    
    @classmethod
    def handles(cls, content: FileContent) -> bool:
        """Detecta si el contenido es un ZIP con XMLs."""
        return content.extension == "zip" and content.parsed_data and "xml_files" in content.parsed_data
    
    async def parse(self, content: FileContent, db) -> FelParsedResult:
        """
        Procesa cada XML del ZIP individualmente usando XmlFelStrategy.
        Retorna un resultado agregado con todos los XMLs procesados.
        """
        xml_files = content.parsed_data.get("xml_files", [])
        
        if not xml_files:
            return FelParsedResult(
                success=False,
                error="El ZIP no contiene archivos XML",
                source_format="zip"
            )
        
        logger.info(f"📦 Procesando ZIP con {len(xml_files)} XMLs")
        
        # Procesar cada XML individualmente
        parsed_results = []
        exitos = 0
        errores = []
        
        xml_strategy = XmlFelStrategy()
        
        for xml_data in xml_files:
            try:
                # Crear FileContent temporal para este XML
                xml_content = FileContent(
                    raw_bytes=xml_data["raw_bytes"],
                    filename=xml_data["filename"],
                    mime_type="application/xml",
                    extension="xml",
                    parsed_data={"xml_text": xml_data["xml_text"]}
                )
                
                # Parsear usando XmlFelStrategy
                result = await xml_strategy.parse(xml_content, db)
                
                if result.success:
                    exitos += 1
                    parsed_results.append({
                        "filename": xml_data["filename"],
                        "success": True,
                        "data": result.data,
                        "source_format": result.source_format
                    })
                else:
                    errores.append({
                        "filename": xml_data["filename"],
                        "error": result.error
                    })
                    parsed_results.append({
                        "filename": xml_data["filename"],
                        "success": False,
                        "error": result.error
                    })
                    
            except Exception as e:
                logger.error(f"Error procesando {xml_data['filename']}: {e}", exc_info=True)
                errores.append({
                    "filename": xml_data["filename"],
                    "error": str(e)
                })
                parsed_results.append({
                    "filename": xml_data["filename"],
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(f"✅ ZIP procesado: {exitos} éxitos, {len(errores)} errores")
        
        # Retornar resultado agregado
        return FelParsedResult(
            success=exitos > 0,
            data={
                "xml_files": xml_files,
                "parsed_results": parsed_results,
                "total_files": len(xml_files),
                "exitos": exitos,
                "errores": errores
            },
            source_format="zip",
            error=f"{len(errores)} XMLs con errores" if errores else None
        )