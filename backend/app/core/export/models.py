"""
Modelos de datos para la arquitectura de exportación genérica.
Define la estructura de cualquier reporte que pueda ser exportado a Excel/PDF.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List


class ColumnAlignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class ColumnType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    PERCENTAGE = "percentage"


@dataclass
class Column:
    """Define una columna del reporte."""
    header: str
    key: str  # key en el dict de datos
    width: float | None = None  # ancho en Excel (chars) / PDF (inches)
    alignment: ColumnAlignment = ColumnAlignment.LEFT
    type: ColumnType = ColumnType.TEXT
    bold_header: bool = True


@dataclass
class Row:
    """Una fila de datos del reporte."""
    data: dict[str, Any]
    bold: bool = False
    italic: bool = False
    background_color: str | None = None  # hex, ej: "#FFFFCC"
    text_color: str | None = None
    indent_level: int = 0  # para jerarquías (ej: plan de cuentas)


@dataclass
class Section:
    """
    Sección del reporte. Permite agrupar filas con un título.
    Ej: "ACTIVOS", "PASIVOS", "INGRESOS"
    """
    title: str
    rows: List[Row] = field(default_factory=list)
    totals: dict[str, Any] | None = None  # fila de totales de la sección
    bold_title: bool = True
    background_color_title: str | None = "#4472C4"
    text_color_title: str | None = "FFFFFF"


@dataclass
class ReportDefinition:
    """
    Definición completa de un reporte.
    Es la estructura genérica que los exporters consumen.
    """
    title: str
    subtitle: str | None = None
    columns: List[Column] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)
    
    # Metadata (aparece en header/footer)
    generated_at: datetime | None = None
    generated_by: str | None = None
    company_name: str | None = None
    period: str | None = None  # ej: "Enero 2026"
    
    # Configuración de página (PDF)
    page_size: str = "letter"  # letter, legal, A4
    orientation: str = "portrait"  # portrait, landscape
    margin_top: float = 0.75  # inches
    margin_bottom: float = 0.75
    margin_left: float = 0.75
    margin_right: float = 0.75
    
    # Configuración Excel
    freeze_panes: str | None = "A2"  # ej: "A2" congela header
    auto_filter: bool = True
    print_area: str | None = None
    
    # Estilos globales
    header_background: str = "#4472C4"
    header_text_color: str = "FFFFFF"
    alternate_row_color: str | None = "#F2F2F2"  # cebra
    border_style: str = "thin"