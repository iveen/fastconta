"""
Exportador genérico a PDF usando reportlab.
Consume un ReportDefinition y produce un buffer BytesIO.
"""
import io
from datetime import date, datetime
from decimal import Decimal

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, legal, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .models import ColumnAlignment, ColumnType, ReportDefinition

# Mapeo de tamaños de página
PAGE_SIZES = {
    "letter": letter,
    "legal": legal,
    "a4": A4,
}


class PdfExporter:
    """Exporta cualquier ReportDefinition a PDF."""
    
    @staticmethod
    def export(report: ReportDefinition) -> io.BytesIO:
        buffer = io.BytesIO()
        
        page_size = PAGE_SIZES.get(report.page_size.lower(), letter)
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=page_size,
            topMargin=report.margin_top * inch,
            bottomMargin=report.margin_bottom * inch,
            leftMargin=report.margin_left * inch,
            rightMargin=report.margin_right * inch,
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Title'],
            fontSize=16,
            spaceAfter=6,
            alignment=TA_CENTER,
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#666666"),
            alignment=TA_CENTER,
            spaceAfter=12,
        )
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=12,
            textColor=colors.white,
            backColor=colors.HexColor("#4472C4"),
            spaceBefore=12,
            spaceAfter=6,
            leftIndent=4,
            rightIndent=4,
        )
        
        # ===== HEADER =====
        elements.append(Paragraph(report.title, title_style))
        
        if report.subtitle:
            elements.append(Paragraph(report.subtitle, subtitle_style))
        
        if report.company_name or report.period:
            meta_parts = []
            if report.company_name:
                meta_parts.append(f"Empresa: {report.company_name}")
            if report.period:
                meta_parts.append(f"Período: {report.period}")
            meta_text = " | ".join(meta_parts)
            elements.append(Paragraph(
                meta_text,
                ParagraphStyle('Meta', parent=styles['Normal'], 
                              fontSize=9, textColor=colors.HexColor("#666666"),
                              alignment=TA_CENTER)
            ))
        
        elements.append(Spacer(1, 0.25 * inch))
        
        # ===== SECCIONES =====
        for section in report.sections:
            if section.title:
                elements.append(Paragraph(section.title, section_style))
            
            # Construir tabla
            headers = [col.header for col in report.columns]
            table_data = [headers]
            
            for row in section.rows:
                table_row = []
                for col in report.columns:
                    value = row.data.get(col.key, "")
                    value = PdfExporter._format_value(value, col.type)
                    table_row.append(str(value))
                table_data.append(table_row)
            
            if section.totals:
                total_row = []
                for col in report.columns:
                    value = section.totals.get(col.key, "")
                    value = PdfExporter._format_value(value, col.type)
                    total_row.append(str(value))
                table_data.append(total_row)
            
            # Calcular anchos de columna
            col_widths = []
            for col in report.columns:
                if col.width:
                    col_widths.append(col.width * inch)
                else:
                    col_widths.append(1.5 * inch)  # default
            
            table = Table(table_data, colWidths=col_widths)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(report.header_background)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(report.header_text_color)),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            
            # Alineación por columna
            for col_idx, col in enumerate(report.columns):
                align = 'LEFT'
                if col.alignment == ColumnAlignment.RIGHT:
                    align = 'RIGHT'
                elif col.alignment == ColumnAlignment.CENTER:
                    align = 'CENTER'
                table.setStyle(TableStyle([
                    ('ALIGN', (col_idx, 1), (col_idx, -1), align),
                ]))
            
            # Fila de totales en bold
            if section.totals:
                last_row_idx = len(table_data) - 1
                table.setStyle(TableStyle([
                    ('FONTNAME', (0, last_row_idx), (-1, last_row_idx), 'Helvetica-Bold'),
                    ('BACKGROUND', (0, last_row_idx), (-1, last_row_idx), colors.HexColor("#E8E8E8")),
                ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.2 * inch))
        
        # ===== FOOTER =====
        if report.generated_at:
            elements.append(Spacer(1, 0.25 * inch))
            footer_text = f"Generado el {report.generated_at.strftime('%d/%m/%Y %H:%M')}"
            if report.generated_by:
                footer_text += f" por {report.generated_by}"
            elements.append(Paragraph(
                footer_text,
                ParagraphStyle('Footer', parent=styles['Normal'],
                              fontSize=8, textColor=colors.HexColor("#999999"),
                              alignment=TA_CENTER)
            ))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer
    
    @staticmethod
    def _format_value(value, col_type: ColumnType) -> str:
        if value is None:
            return ""
        if col_type == ColumnType.CURRENCY:
            if isinstance(value, Decimal):
                return f"{float(value):,.2f}"
            return f"{float(value):,.2f}" if isinstance(value, (int, float)) else str(value)
        if col_type == ColumnType.NUMBER:
            if isinstance(value, Decimal):
                return f"{float(value):,.2f}"
            return str(value)
        if col_type == ColumnType.DATE:
            if isinstance(value, (date, datetime)):
                return value.strftime("%d/%m/%Y")
            return str(value)
        return str(value)