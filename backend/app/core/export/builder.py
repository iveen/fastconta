"""
Builder pattern para construir ReportDefinitions de forma fluida.
Ejemplo de uso:
    report = (ReportBuilder()
        .title("Balance de Comprobación")
        .subtitle("Enero 2026")
        .columns([...])
        .add_section("ACTIVOS", rows, totals={...})
        .add_section("PASIVOS", rows, totals={...})
        .build())
"""
from datetime import datetime
from typing import Any, List

from .models import Column, ReportDefinition, Row, Section


class ReportBuilder:
    def __init__(self):
        self._title = ""
        self._subtitle: str | None = None
        self._columns: List[Column] = []
        self._sections: List[Section] = []
        self._company_name: str | None = None
        self._period: str | None = None
        self._generated_by: str | None = None
        self._orientation = "portrait"
        self._freeze_panes = "A2"
    
    def title(self, title: str) -> "ReportBuilder":
        self._title = title
        return self
    
    def subtitle(self, subtitle: str) -> "ReportBuilder":
        self._subtitle = subtitle
        return self
    
    def company(self, name: str) -> "ReportBuilder":
        self._company_name = name
        return self
    
    def period(self, period: str) -> "ReportBuilder":
        self._period = period
        return self
    
    def generated_by(self, user: str) -> "ReportBuilder":
        self._generated_by = user
        return self
    
    def orientation(self, orientation: str) -> "ReportBuilder":
        self._orientation = orientation
        return self
    
    def freeze_panes(self, cell: str) -> "ReportBuilder":
        self._freeze_panes = cell
        return self
    
    def columns(self, columns: List[Column]) -> "ReportBuilder":
        self._columns = columns
        return self
    
    def add_column(self, column: Column) -> "ReportBuilder":
        self._columns.append(column)
        return self
    
    def add_section(
        self,
        title: str,
        rows: List[Row],
        totals: dict[str, Any] | None = None,
        bold_title: bool = True,
    ) -> "ReportBuilder":
        self._sections.append(Section(
            title=title,
            rows=rows,
            totals=totals,
            bold_title=bold_title,
        ))
        return self
    
    def add_rows(self, rows: List[Row]) -> "ReportBuilder":
        """Agrega filas a una sección sin título (reporte plano)."""
        if not self._sections or self._sections[-1].title:
            self._sections.append(Section(title="", rows=[]))
        self._sections[-1].rows.extend(rows)
        return self
    
    def build(self) -> ReportDefinition:
        return ReportDefinition(
            title=self._title,
            subtitle=self._subtitle,
            columns=self._columns,
            sections=self._sections,
            generated_at=datetime.utcnow(),
            generated_by=self._generated_by,
            company_name=self._company_name,
            period=self._period,
            orientation=self._orientation,
            freeze_panes=self._freeze_panes,
        )