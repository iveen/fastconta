"""
Módulo de exportación genérica.
Permite generar Excel y PDF desde cualquier parte del sistema.

Ejemplo de uso:
    from app.core.export import ReportBuilder, ExcelExporter, PdfExporter
    
    report = (ReportBuilder()
        .title("Balance de Comprobación")
        .columns([...])
        .add_section("ACTIVOS", rows)
        .build())
    
    excel_buffer = ExcelExporter.export(report)
    pdf_buffer = PdfExporter.export(report)
"""
from .builder import ReportBuilder
from .excel_exporter import ExcelExporter
from .models import Column, ColumnAlignment, ColumnType, ReportDefinition, Row, Section
from .pdf_exporter import PdfExporter

__all__ = [
    "Column",
    "ColumnAlignment",
    "ColumnType",
    "ReportDefinition",
    "Row",
    "Section",
    "ReportBuilder",
    "ExcelExporter",
    "PdfExporter",
]