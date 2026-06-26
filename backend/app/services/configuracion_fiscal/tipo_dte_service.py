"""Servicio para gestión de Tipos DTE"""

from io import BytesIO
from typing import Any
from uuid import UUID

from app.models.global_models import TipoDTE
from app.utils.excel_handler import ExcelHandler
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Columnas para exportación
COLUMNAS_EXPORT = [
    {"key": "codigo", "header": "Código", "width": 12},
    {"key": "descripcion", "header": "Descripción", "width": 40},
    {"key": "requiere_complemento", "header": "Requiere Complemento", "width": 20},
    {"key": "es_factura", "header": "Es Factura", "width": 12},
    {"key": "activo", "header": "Activo", "width": 10},
]

COLUMNAS_IMPORT_REQUERIDAS = ["codigo", "descripcion", "requiere_complemento", "es_factura"]


class TipoDTEService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_todos(
        self,
        activo: bool | None = None,
        es_factura: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[TipoDTE], int]:
        """Lista tipos DTE con filtros"""
        query = select(TipoDTE)

        if activo is not None:
            query = query.where(TipoDTE.activo.is_(activo))
        if es_factura is not None:
            query = query.where(TipoDTE.es_factura.is_(es_factura))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(TipoDTE.codigo).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_por_id(self, dte_id: UUID) -> TipoDTE | None:
        """Obtiene un tipo DTE por ID"""
        query = select(TipoDTE).where(TipoDTE.id == dte_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_por_codigo(self, codigo: str) -> TipoDTE | None:
        """Obtiene un tipo DTE por código"""
        query = select(TipoDTE).where(TipoDTE.codigo == codigo)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_todos_activos(self) -> list[TipoDTE]:
        """Obtiene todos los tipos DTE activos (para dropdowns)"""
        query = (
            select(TipoDTE)
            .where(TipoDTE.activo.is_(True))
            .order_by(TipoDTE.codigo)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # CRUD
    # ============================================================
    async def crear(self, data: dict) -> TipoDTE:
        """Crea un nuevo tipo DTE"""
        # Validar código único
        existente = await self.obtener_por_codigo(data["codigo"])
        if existente is not None:
            raise ValueError(f"Ya existe un tipo DTE con código '{data['codigo']}'")

        dte = TipoDTE(**data)
        self.db.add(dte)
        await self.db.flush()
        await self.db.refresh(dte)
        return dte

    async def actualizar(
        self, dte_id: UUID, data: dict
    ) -> TipoDTE | None:
        """Actualiza un tipo DTE"""
        dte = await self.obtener_por_id(dte_id)
        if dte is None:
            return None

        for key, value in data.items():
            if hasattr(dte, key):
                setattr(dte, key, value)

        await self.db.flush()
        await self.db.refresh(dte)
        return dte

    async def eliminar(self, dte_id: UUID) -> bool:
        """Soft delete (activo = False)"""
        dte = await self.obtener_por_id(dte_id)
        if dte is None:
            return False

        dte.activo = False
        await self.db.flush()
        return True

    # ============================================================
    # IMPORT/EXPORT
    # ============================================================
    async def exportar_excel(self) -> BytesIO:
        """Exporta todos los tipos DTE a Excel"""
        dtes = await self.obtener_todos_activos()
        
        datos = [
            {
                "codigo": dte.codigo,
                "descripcion": dte.descripcion,
                "requiere_complemento": "Sí" if dte.requiere_complemento else "No",
                "es_factura": "Sí" if dte.es_factura else "No",
                "activo": "Sí" if dte.activo else "No",
            }
            for dte in dtes
        ]

        return ExcelHandler.exportar_a_excel(
            datos=datos,
            columnas=COLUMNAS_EXPORT,
            nombre_hoja="Tipos DTE",
            titulo="Catálogo de Tipos de Documentos Tributarios Electrónicos",
        )

    async def importar_excel(
        self,
        archivo_bytes: bytes,
        sobrescribir: bool = False,
    ) -> dict:
        """
        Importa tipos DTE desde Excel.
        
        Returns:
            Dict con estadísticas de importación
        """
        try:
            filas = ExcelHandler.importar_desde_excel(
                archivo_bytes=archivo_bytes,
                columnas_requeridas=COLUMNAS_IMPORT_REQUERIDAS,
            )
        except ValueError as e:
            raise ValueError(str(e))

        creados = 0
        actualizados = 0
        omitidos = 0
        errores: list[str] = []

        for idx, fila in enumerate(filas, 2):  # Empezar en 2 (fila 1 = encabezados)
            try:
                codigo = str(fila.get("codigo", "")).strip()
                descripcion = str(fila.get("descripcion", "")).strip()
                
                # Parsear booleanos
                requiere_complemento = self._parse_bool(fila.get("requiere_complemento", False))
                es_factura = self._parse_bool(fila.get("es_factura", True))

                if not codigo or not descripcion:
                    errores.append(f"Fila {idx}: Código y descripción son obligatorios")
                    continue

                # Validar longitud
                if len(codigo) > 10:
                    errores.append(f"Fila {idx}: Código '{codigo}' excede 10 caracteres")
                    continue

                if len(descripcion) > 100:
                    errores.append(f"Fila {idx}: Descripción excede 100 caracteres")
                    continue

                # Buscar existente
                existente = await self.obtener_por_codigo(codigo)

                if existente is not None:
                    if sobrescribir:
                        existente.descripcion = descripcion
                        existente.requiere_complemento = requiere_complemento
                        existente.es_factura = es_factura
                        existente.activo = True
                        actualizados += 1
                    else:
                        omitidos += 1
                else:
                    dte = TipoDTE(
                        codigo=codigo,
                        descripcion=descripcion,
                        requiere_complemento=requiere_complemento,
                        es_factura=es_factura,
                        activo=True,
                    )
                    self.db.add(dte)
                    creados += 1

            except Exception as e:
                errores.append(f"Fila {idx}: {str(e)}")

        await self.db.flush()

        return {
            "creados": creados,
            "actualizados": actualizados,
            "omitidos": omitidos,
            "errores": errores,
        }

    @staticmethod
    def _parse_bool(valor: Any) -> bool:
        """Parsea valores booleanos desde Excel"""
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, str):
            return valor.lower() in ("sí", "si", "true", "1", "yes", "s")
        if isinstance(valor, (int, float)):
            return bool(valor)
        return False