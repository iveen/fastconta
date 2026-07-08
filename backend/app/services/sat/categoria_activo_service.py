"""Servicio para gestión de Categorías de Activos Fijos"""

from io import BytesIO
from uuid import UUID

from app.models.global_models import CategoriaActivoFijo
from app.utils.excel_handler import ExcelHandler
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Columnas para exportación
COLUMNAS_EXPORT = [
    {"key": "nombre", "header": "Nombre de la Categoría", "width": 30},
    {"key": "codigo_prefijo", "header": "Prefijo", "width": 12},
    {"key": "tasa_minima_anual", "header": "Tasa Mínima (%)", "width": 15},
    {"key": "tasa_maxima_anual", "header": "Tasa Máxima (%)", "width": 15},
    {"key": "vida_util_meses_default", "header": "Vida Útil (meses)", "width": 18},
    {"key": "descripcion", "header": "Descripción Legal", "width": 50},
    {"key": "is_active", "header": "Activa", "width": 10},
]

COLUMNAS_IMPORT_REQUERIDAS = [
    "nombre",
    "tasa_minima_anual",
    "tasa_maxima_anual",
    "vida_util_meses_default",
    "codigo_prefijo",
]


class CategoriaActivoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_todos(
        self,
        is_active: bool | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[CategoriaActivoFijo], int]:
        """Lista categorías con filtros"""
        query = select(CategoriaActivoFijo)

        if is_active is not None:
            query = query.where(CategoriaActivoFijo.is_active.is_(is_active))
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (CategoriaActivoFijo.nombre.ilike(search_pattern))
                | (CategoriaActivoFijo.codigo_prefijo.ilike(search_pattern))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(CategoriaActivoFijo.nombre).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_por_id(
        self, categoria_id: UUID
    ) -> CategoriaActivoFijo | None:
        """Obtiene una categoría por ID"""
        query = select(CategoriaActivoFijo).where(
            CategoriaActivoFijo.id == categoria_id
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_por_nombre(self, nombre: str) -> CategoriaActivoFijo | None:
        """Obtiene una categoría por nombre"""
        query = select(CategoriaActivoFijo).where(
            CategoriaActivoFijo.nombre == nombre
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_por_prefijo(self, prefijo: str) -> CategoriaActivoFijo | None:
        """Obtiene una categoría por prefijo"""
        query = select(CategoriaActivoFijo).where(
            CategoriaActivoFijo.codigo_prefijo == prefijo
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_todas_activas(self) -> list[CategoriaActivoFijo]:
        """Obtiene todas las categorías activas (para dropdowns)"""
        query = (
            select(CategoriaActivoFijo)
            .where(CategoriaActivoFijo.is_active.is_(True))
            .order_by(CategoriaActivoFijo.nombre)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # CRUD
    # ============================================================
    async def crear(self, data: dict) -> CategoriaActivoFijo:
        """Crea una nueva categoría"""
        # Validar nombre único
        existente_nombre = await self.obtener_por_nombre(data["nombre"])
        if existente_nombre is not None:
            raise ValueError(f"Ya existe una categoría con nombre '{data['nombre']}'")

        # Validar prefijo único
        existente_prefijo = await self.obtener_por_prefijo(data["codigo_prefijo"])
        if existente_prefijo is not None:
            raise ValueError(
                f"Ya existe una categoría con prefijo '{data['codigo_prefijo']}'"
            )

        # Validar tasas
        if data["tasa_maxima_anual"] < data["tasa_minima_anual"]:
            raise ValueError(
                "La tasa máxima anual debe ser mayor o igual a la tasa mínima anual"
            )

        categoria = CategoriaActivoFijo(**data)
        self.db.add(categoria)
        await self.db.flush()
        await self.db.refresh(categoria)
        return categoria

    async def actualizar(
        self, categoria_id: UUID, data: dict
    ) -> CategoriaActivoFijo | None:
        """Actualiza una categoría"""
        categoria = await self.obtener_por_id(categoria_id)
        if categoria is None:
            return None

        # Validar nombre único si cambia
        if "nombre" in data and data["nombre"] != categoria.nombre:
            existente = await self.obtener_por_nombre(data["nombre"])
            if existente is not None:
                raise ValueError(
                    f"Ya existe una categoría con nombre '{data['nombre']}'"
                )

        # Validar prefijo único si cambia
        if "codigo_prefijo" in data and data["codigo_prefijo"] != categoria.codigo_prefijo:
            existente = await self.obtener_por_prefijo(data["codigo_prefijo"])
            if existente is not None:
                raise ValueError(
                    f"Ya existe una categoría con prefijo '{data['codigo_prefijo']}'"
                )

        # Validar tasas si ambas cambian
        tasa_min = data.get("tasa_minima_anual", categoria.tasa_minima_anual)
        tasa_max = data.get("tasa_maxima_anual", categoria.tasa_maxima_anual)
        if tasa_max < tasa_min:
            raise ValueError(
                "La tasa máxima anual debe ser mayor o igual a la tasa mínima anual"
            )

        for key, value in data.items():
            if hasattr(categoria, key):
                setattr(categoria, key, value)

        await self.db.flush()
        await self.db.refresh(categoria)
        return categoria

    async def eliminar(self, categoria_id: UUID) -> bool:
        """Soft delete (is_active = False)"""
        categoria = await self.obtener_por_id(categoria_id)
        if categoria is None:
            return False

        categoria.is_active = False
        await self.db.flush()
        return True

    # ============================================================
    # IMPORT/EXPORT
    # ============================================================
    async def exportar_excel(self) -> BytesIO:
        """Exporta todas las categorías a Excel"""
        categorias = await self.obtener_todas_activas()

        datos = [
            {
                "nombre": cat.nombre,
                "codigo_prefijo": cat.codigo_prefijo,
                "tasa_minima_anual": float(cat.tasa_minima_anual),
                "tasa_maxima_anual": float(cat.tasa_maxima_anual),
                "vida_util_meses_default": cat.vida_util_meses_default,
                "descripcion": cat.descripcion or "",
                "is_active": "Sí" if cat.is_active else "No",
            }
            for cat in categorias
        ]

        return ExcelHandler.exportar_a_excel(
            datos=datos,
            columnas=COLUMNAS_EXPORT,
            nombre_hoja="Categorías Activos",
            titulo="Catálogo de Categorías de Activos Fijos (Decreto 10-2012)",
        )

    async def importar_excel(
        self,
        archivo_bytes: bytes,
        sobrescribir: bool = False,
    ) -> dict:
        """
        Importa categorías desde Excel.

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
                nombre = str(fila.get("nombre", "")).strip()
                descripcion = str(fila.get("descripcion", "")).strip() or None
                codigo_prefijo = str(fila.get("codigo_prefijo", "")).strip()

                # Parsear valores numéricos
                try:
                    tasa_minima = float(fila.get("tasa_minima_anual", 0))
                    tasa_maxima = float(fila.get("tasa_maxima_anual", 0))
                    vida_util = int(fila.get("vida_util_meses_default", 0))
                except (ValueError, TypeError) as e:
                    errores.append(f"Fila {idx}: Valores numéricos inválidos - {e}")
                    continue

                # Validaciones
                if not nombre:
                    errores.append(f"Fila {idx}: Nombre es obligatorio")
                    continue

                if len(nombre) > 100:
                    errores.append(f"Fila {idx}: Nombre excede 100 caracteres")
                    continue

                if not codigo_prefijo:
                    errores.append(f"Fila {idx}: Código prefijo es obligatorio")
                    continue

                if len(codigo_prefijo) > 10:
                    errores.append(f"Fila {idx}: Prefijo excede 10 caracteres")
                    continue

                if tasa_minima < 0 or tasa_minima > 100:
                    errores.append(f"Fila {idx}: Tasa mínima debe estar entre 0 y 100")
                    continue

                if tasa_maxima < 0 or tasa_maxima > 100:
                    errores.append(f"Fila {idx}: Tasa máxima debe estar entre 0 y 100")
                    continue

                if tasa_maxima < tasa_minima:
                    errores.append(
                        f"Fila {idx}: Tasa máxima debe ser >= tasa mínima"
                    )
                    continue

                if vida_util <= 0:
                    errores.append(f"Fila {idx}: Vida útil debe ser mayor a 0")
                    continue

                # Buscar existente por nombre
                existente = await self.obtener_por_nombre(nombre)

                if existente is not None:
                    if sobrescribir:
                        existente.descripcion = descripcion
                        existente.tasa_minima_anual = tasa_minima
                        existente.tasa_maxima_anual = tasa_maxima
                        existente.vida_util_meses_default = vida_util
                        existente.codigo_prefijo = codigo_prefijo
                        existente.is_active = True
                        actualizados += 1
                    else:
                        omitidos += 1
                else:
                    categoria = CategoriaActivoFijo(
                        nombre=nombre,
                        descripcion=descripcion,
                        tasa_minima_anual=tasa_minima,
                        tasa_maxima_anual=tasa_maxima,
                        vida_util_meses_default=vida_util,
                        codigo_prefijo=codigo_prefijo,
                        is_active=True,
                    )
                    self.db.add(categoria)
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