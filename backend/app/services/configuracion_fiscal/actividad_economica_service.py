"""Servicio para gestión de Actividades Económicas SAT"""

from io import BytesIO
from uuid import UUID

from app.models.global_models import ActividadEconomicaSAT
from app.utils.excel_handler import ExcelHandler
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Columnas para exportación
COLUMNAS_EXPORT = [
    {"key": "codigo_sat", "header": "Código SAT", "width": 15},
    {"key": "nombre_actividad", "header": "Nombre de la Actividad", "width": 50},
    {"key": "seccion", "header": "Sección", "width": 30},
    {"key": "activa", "header": "Activa", "width": 10},
]

COLUMNAS_IMPORT_REQUERIDAS = ["codigo_sat", "nombre_actividad"]


class ActividadEconomicaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_todos(
        self,
        activa: bool | None = None,
        seccion: str | None = None,
        search: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[ActividadEconomicaSAT], int]:
        """Lista actividades económicas con filtros"""
        query = select(ActividadEconomicaSAT)

        if activa is not None:
            query = query.where(ActividadEconomicaSAT.activa.is_(activa))
        if seccion:
            query = query.where(ActividadEconomicaSAT.seccion == seccion)
        if search:
            search_pattern = f"%{search}%"
            query = query.where(
                (ActividadEconomicaSAT.codigo_sat.ilike(search_pattern))
                | (ActividadEconomicaSAT.nombre_actividad.ilike(search_pattern))
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(ActividadEconomicaSAT.codigo_sat).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_por_id(self, actividad_id: UUID) -> ActividadEconomicaSAT | None:
        """Obtiene una actividad económica por ID"""
        query = select(ActividadEconomicaSAT).where(
            ActividadEconomicaSAT.id == actividad_id
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_por_codigo(self, codigo_sat: str) -> ActividadEconomicaSAT | None:
        """Obtiene una actividad económica por código SAT"""
        query = select(ActividadEconomicaSAT).where(
            ActividadEconomicaSAT.codigo_sat == codigo_sat
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_todas_activas(self) -> list[ActividadEconomicaSAT]:
        """Obtiene todas las actividades económicas activas (para dropdowns)"""
        query = (
            select(ActividadEconomicaSAT)
            .where(ActividadEconomicaSAT.activa.is_(True))
            .order_by(ActividadEconomicaSAT.codigo_sat)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def obtener_secciones_unicas(self) -> list[str]:
        """Obtiene lista de secciones únicas (para filtros)"""
        query = (
            select(ActividadEconomicaSAT.seccion)
            .where(
                ActividadEconomicaSAT.seccion.isnot(None),
                ActividadEconomicaSAT.activa.is_(True),
            )
            .distinct()
            .order_by(ActividadEconomicaSAT.seccion)
        )
        result = await self.db.execute(query)
        return [row[0] for row in result.all() if row[0]]

    # ============================================================
    # CRUD
    # ============================================================
    async def crear(self, data: dict) -> ActividadEconomicaSAT:
        """Crea una nueva actividad económica"""
        # Validar código único
        existente = await self.obtener_por_codigo(data["codigo_sat"])
        if existente is not None:
            raise ValueError(f"Ya existe una actividad con código SAT '{data['codigo_sat']}'")

        actividad = ActividadEconomicaSAT(**data)
        self.db.add(actividad)
        await self.db.flush()
        await self.db.refresh(actividad)
        return actividad

    async def actualizar(
        self, actividad_id: UUID, data: dict
    ) -> ActividadEconomicaSAT | None:
        """Actualiza una actividad económica"""
        actividad = await self.obtener_por_id(actividad_id)
        if actividad is None:
            return None

        for key, value in data.items():
            if hasattr(actividad, key):
                setattr(actividad, key, value)

        await self.db.flush()
        await self.db.refresh(actividad)
        return actividad

    async def eliminar(self, actividad_id: UUID) -> bool:
        """Soft delete (activa = False)"""
        actividad = await self.obtener_por_id(actividad_id)
        if actividad is None:
            return False

        actividad.activa = False
        await self.db.flush()
        return True

    # ============================================================
    # IMPORT/EXPORT
    # ============================================================
    async def exportar_excel(self) -> BytesIO:
        """Exporta todas las actividades económicas a Excel"""
        actividades = await self.obtener_todas_activas()
        
        datos = [
            {
                "codigo_sat": act.codigo_sat,
                "nombre_actividad": act.nombre_actividad,
                "seccion": act.seccion or "",
                "activa": "Sí" if act.activa else "No",
            }
            for act in actividades
        ]

        return ExcelHandler.exportar_a_excel(
            datos=datos,
            columnas=COLUMNAS_EXPORT,
            nombre_hoja="Actividades Económicas",
            titulo="Catálogo de Actividades Económicas SAT",
        )

    async def importar_excel(
        self,
        archivo_bytes: bytes,
        sobrescribir: bool = False,
    ) -> dict:
        """
        Importa actividades económicas desde Excel.
        
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
                codigo_sat = str(fila.get("codigo_sat", "")).strip()
                nombre_actividad = str(fila.get("nombre_actividad", "")).strip()
                seccion = str(fila.get("seccion", "")).strip() if fila.get("seccion") else None

                if not codigo_sat or not nombre_actividad:
                    errores.append(f"Fila {idx}: Código SAT y nombre son obligatorios")
                    continue

                # Validar longitud
                if len(codigo_sat) > 20:
                    errores.append(f"Fila {idx}: Código SAT '{codigo_sat}' excede 20 caracteres")
                    continue

                if len(nombre_actividad) > 255:
                    errores.append(f"Fila {idx}: Nombre excede 255 caracteres")
                    continue

                if seccion and len(seccion) > 255:
                    errores.append(f"Fila {idx}: Sección excede 255 caracteres")
                    continue

                # Buscar existente
                existente = await self.obtener_por_codigo(codigo_sat)

                if existente is not None:
                    if sobrescribir:
                        existente.nombre_actividad = nombre_actividad
                        existente.seccion = seccion
                        existente.activa = True
                        actualizados += 1
                    else:
                        omitidos += 1
                else:
                    actividad = ActividadEconomicaSAT(
                        codigo_sat=codigo_sat,
                        nombre_actividad=nombre_actividad,
                        seccion=seccion,
                        activa=True,
                    )
                    self.db.add(actividad)
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