"""Servicio para gestión de Catálogo de Monedas"""

from io import BytesIO
from uuid import UUID

from app.models.global_models import CatalogoMoneda
from app.utils.excel_handler import ExcelHandler
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Columnas para exportación
COLUMNAS_EXPORT = [
    {"key": "codigo_banguat", "header": "Código Banguat", "width": 15},
    {"key": "codigo_iso", "header": "Código ISO", "width": 12},
    {"key": "nombre", "header": "Nombre de la Moneda", "width": 30},
    {"key": "simbolo", "header": "Símbolo", "width": 10},
    {"key": "decimales", "header": "Decimales", "width": 12},
    {"key": "activo", "header": "Activa", "width": 10},
]

COLUMNAS_IMPORT_REQUERIDAS = [
    "codigo_banguat",
    "codigo_iso",
    "nombre",
]


class CatalogoMonedaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_todos(
        self,
        activo: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CatalogoMoneda], int]:
        """Lista monedas con filtros"""
        query = select(CatalogoMoneda)

        if activo is not None:
            query = query.where(CatalogoMoneda.activo.is_(activo))
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (CatalogoMoneda.nombre.ilike(search_pattern))
                | (CatalogoMoneda.codigo_iso.ilike(search_pattern))
                | (CatalogoMoneda.codigo_banguat.ilike(search_pattern))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(CatalogoMoneda.codigo_banguat).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_por_id(self, moneda_id: UUID) -> CatalogoMoneda | None:
        """Obtiene una moneda por ID"""
        query = select(CatalogoMoneda).where(CatalogoMoneda.id == moneda_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_por_codigo_iso(self, codigo_iso: str) -> CatalogoMoneda | None:
        """Obtiene una moneda por código ISO"""
        query = select(CatalogoMoneda).where(
            CatalogoMoneda.codigo_iso == codigo_iso
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_por_codigo_banguat(
        self, codigo_banguat: str
    ) -> CatalogoMoneda | None:
        """Obtiene una moneda por código Banguat"""
        query = select(CatalogoMoneda).where(
            CatalogoMoneda.codigo_banguat == codigo_banguat
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_todas_activas(self) -> list[CatalogoMoneda]:
        """Obtiene todas las monedas activas (para dropdowns)"""
        query = (
            select(CatalogoMoneda)
            .where(CatalogoMoneda.activo.is_(True))
            .order_by(CatalogoMoneda.nombre)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # CRUD
    # ============================================================
    async def crear(self, data: dict) -> CatalogoMoneda:
        """Crea una nueva moneda"""
        # Validar código ISO único
        existente_iso = await self.obtener_por_codigo_iso(data["codigo_iso"])
        if existente_iso is not None:
            raise ValueError(
                f"Ya existe una moneda con código ISO '{data['codigo_iso']}'"
            )

        # Validar código Banguat único
        existente_banguat = await self.obtener_por_codigo_banguat(
            data["codigo_banguat"]
        )
        if existente_banguat is not None:
            raise ValueError(
                f"Ya existe una moneda con código Banguat '{data['codigo_banguat']}'"
            )

        moneda = CatalogoMoneda(**data)
        self.db.add(moneda)
        await self.db.flush()
        await self.db.refresh(moneda)
        return moneda

    async def actualizar(
        self, moneda_id: UUID, data: dict
    ) -> CatalogoMoneda | None:
        """Actualiza una moneda"""
        moneda = await self.obtener_por_id(moneda_id)
        if moneda is None:
            return None

        # Validar código ISO único si cambia
        if "codigo_iso" in data and data["codigo_iso"] != moneda.codigo_iso:
            existente = await self.obtener_por_codigo_iso(data["codigo_iso"])
            if existente is not None:
                raise ValueError(
                    f"Ya existe una moneda con código ISO '{data['codigo_iso']}'"
                )

        # Validar código Banguat único si cambia
        if "codigo_banguat" in data and data["codigo_banguat"] != moneda.codigo_banguat:
            existente = await self.obtener_por_codigo_banguat(data["codigo_banguat"])
            if existente is not None:
                raise ValueError(
                    f"Ya existe una moneda con código Banguat '{data['codigo_banguat']}'"
                )

        for key, value in data.items():
            if hasattr(moneda, key):
                setattr(moneda, key, value)

        await self.db.flush()
        await self.db.refresh(moneda)
        return moneda

    async def eliminar(self, moneda_id: UUID) -> bool:
        """Soft delete (activo = False)"""
        moneda = await self.obtener_por_id(moneda_id)
        if moneda is None:
            return False

        moneda.activo = False
        await self.db.flush()
        return True

    # ============================================================
    # IMPORT/EXPORT
    # ============================================================
    async def exportar_excel(self) -> BytesIO:
        """Exporta todas las monedas a Excel"""
        monedas = await self.obtener_todas_activas()

        datos = [
            {
                "codigo_banguat": mon.codigo_banguat,
                "codigo_iso": mon.codigo_iso,
                "nombre": mon.nombre,
                "simbolo": mon.simbolo or "",
                "decimales": mon.decimales,
                "activo": "Sí" if mon.activo else "No",
            }
            for mon in monedas
        ]

        return ExcelHandler.exportar_a_excel(
            datos=datos,
            columnas=COLUMNAS_EXPORT,
            nombre_hoja="Monedas",
            titulo="Catálogo de Monedas (Banguat / ISO 4217)",
        )

    async def importar_excel(
        self,
        archivo_bytes: bytes,
        sobrescribir: bool = False,
    ) -> dict:
        """
        Importa monedas desde Excel.

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

        for idx, fila in enumerate(filas, 2):
            try:
                codigo_banguat = str(fila.get("codigo_banguat", "")).strip()
                codigo_iso = str(fila.get("codigo_iso", "")).strip().upper()
                nombre = str(fila.get("nombre", "")).strip()
                simbolo = str(fila.get("simbolo", "")).strip() or None

                # Parsear decimales
                try:
                    decimales = int(fila.get("decimales", 2))
                except (ValueError, TypeError):
                    decimales = 2

                # Validaciones
                if not codigo_banguat:
                    errores.append(f"Fila {idx}: Código Banguat es obligatorio")
                    continue

                if len(codigo_banguat) > 5:
                    errores.append(
                        f"Fila {idx}: Código Banguat excede 5 caracteres"
                    )
                    continue

                if not codigo_iso:
                    errores.append(f"Fila {idx}: Código ISO es obligatorio")
                    continue

                if len(codigo_iso) != 3:
                    errores.append(
                        f"Fila {idx}: Código ISO debe tener exactamente 3 caracteres"
                    )
                    continue

                if not nombre:
                    errores.append(f"Fila {idx}: Nombre es obligatorio")
                    continue

                if len(nombre) > 50:
                    errores.append(f"Fila {idx}: Nombre excede 50 caracteres")
                    continue

                if simbolo and len(simbolo) > 5:
                    errores.append(f"Fila {idx}: Símbolo excede 5 caracteres")
                    continue

                if decimales < 0 or decimales > 6:
                    errores.append(
                        f"Fila {idx}: Decimales debe estar entre 0 y 6"
                    )
                    continue

                # Buscar existente por código ISO (clave principal de negocio)
                existente = await self.obtener_por_codigo_iso(codigo_iso)

                if existente is not None:
                    if sobrescribir:
                        existente.codigo_banguat = codigo_banguat
                        existente.nombre = nombre
                        existente.simbolo = simbolo
                        existente.decimales = decimales
                        existente.activo = True
                        actualizados += 1
                    else:
                        omitidos += 1
                else:
                    moneda = CatalogoMoneda(
                        codigo_banguat=codigo_banguat,
                        codigo_iso=codigo_iso,
                        nombre=nombre,
                        simbolo=simbolo,
                        decimales=decimales,
                        activo=True,
                    )
                    self.db.add(moneda)
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