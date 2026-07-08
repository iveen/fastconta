"""Servicio para gestión de Mapeo Casilla-Cuenta"""

from io import BytesIO
from uuid import UUID

from app.models.global_models import CasillaSat, MapeoCasillaCuenta
from app.schemas.sat.mapeo_casilla import TIPOS_MOVIMIENTO
from app.utils.excel_handler import ExcelHandler
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Columnas para exportación
COLUMNAS_EXPORT = [
    {"key": "casilla_codigo", "header": "Código Casilla", "width": 12},
    {"key": "casilla_nombre", "header": "Nombre Casilla", "width": 35},
    {"key": "codigo_cuenta_sugerido", "header": "Código Cuenta", "width": 15},
    {"key": "nombre_cuenta_sugerido", "header": "Nombre Cuenta", "width": 30},
    {"key": "tipo_movimiento", "header": "Movimiento", "width": 12},
    {"key": "ambito", "header": "Ámbito", "width": 10},
]

COLUMNAS_IMPORT_REQUERIDAS = [
    "codigo_casilla",
    "codigo_cuenta_sugerido",
    "nombre_cuenta_sugerido",
    "tipo_movimiento",
]


class MapeoCasillaCuentaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_todos(
        self,
        casilla_id: UUID | None = None,
        tenant_id: UUID | None = None,
        empresa_id: UUID | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[MapeoCasillaCuenta], int]:
        """Lista mapeos con filtros exactos (incluye NULL)"""
        query = (
            select(MapeoCasillaCuenta)
            .options(selectinload(MapeoCasillaCuenta.casilla))
        )

        if casilla_id is not None:
            query = query.where(MapeoCasillaCuenta.casilla_id == casilla_id)
        if tenant_id is not None:
            query = query.where(MapeoCasillaCuenta.tenant_id.is_(tenant_id))
        if empresa_id is not None:
            query = query.where(MapeoCasillaCuenta.empresa_id.is_(empresa_id))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.order_by(MapeoCasillaCuenta.codigo_cuenta_sugerido).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def obtener_por_id(self, mapeo_id: UUID) -> MapeoCasillaCuenta | None:
        """Obtiene un mapeo específico"""
        query = (
            select(MapeoCasillaCuenta)
            .where(MapeoCasillaCuenta.id == mapeo_id)
            .options(selectinload(MapeoCasillaCuenta.casilla))
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_por_casilla(
        self, casilla_id: UUID, tenant_id: UUID | None = None
    ) -> list[MapeoCasillaCuenta]:
        """Obtiene mapeos de una casilla (prioriza tenant específico, fallback global)"""
        query = (
            select(MapeoCasillaCuenta)
            .where(MapeoCasillaCuenta.casilla_id == casilla_id)
            .order_by(MapeoCasillaCuenta.tipo_movimiento)
        )

        if tenant_id is not None:
            # Traer mapeos del tenant O globales
            query = query.where(
                (MapeoCasillaCuenta.tenant_id == tenant_id)
                | (MapeoCasillaCuenta.tenant_id.is_(None))
            )
        else:
            # Solo globales
            query = query.where(MapeoCasillaCuenta.tenant_id.is_(None))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ============================================================
    # CRUD
    # ============================================================
    async def crear(self, data: dict) -> MapeoCasillaCuenta:
        """Crea un nuevo mapeo"""
        # Validar unicidad
        existente = await self._buscar_existente(
            data.get("casilla_id"),
            data.get("tenant_id"),
            data.get("empresa_id"),
        )
        if existente is not None:
            raise ValueError("Ya existe un mapeo con esta combinación de casilla, tenant y empresa.")

        # Validar casilla
        casilla_query = select(CasillaSat).where(CasillaSat.id == data["casilla_id"])
        if (await self.db.execute(casilla_query)).scalars().first() is None:
            raise ValueError("Casilla no encontrada")

        mapeo = MapeoCasillaCuenta(**data)
        self.db.add(mapeo)
        await self.db.flush()
        await self.db.refresh(mapeo)
        return mapeo

    async def actualizar(
        self, mapeo_id: UUID, data: dict
    ) -> MapeoCasillaCuenta | None:
        """Actualiza un mapeo"""
        mapeo = await self.obtener_por_id(mapeo_id)
        if mapeo is None:
            return None

        # Validar unicidad si cambian las llaves de negocio
        if any(k in data for k in ("casilla_id", "tenant_id", "empresa_id")):
            nuevo_casilla = data.get("casilla_id", mapeo.casilla_id)
            nuevo_tenant = data.get("tenant_id", mapeo.tenant_id)
            nuevo_empresa = data.get("empresa_id", mapeo.empresa_id)

            existente = await self._buscar_existente(
                nuevo_casilla, nuevo_tenant, nuevo_empresa, exclude_id=mapeo_id
            )
            if existente is not None:
                raise ValueError("Ya existe otro mapeo con esta combinación.")

        for key, value in data.items():
            if hasattr(mapeo, key):
                setattr(mapeo, key, value)

        await self.db.flush()
        await self.db.refresh(mapeo)
        return mapeo

    async def eliminar(self, mapeo_id: UUID) -> bool:
        """Elimina un mapeo"""
        mapeo = await self.obtener_por_id(mapeo_id)
        if mapeo is None:
            return False

        await self.db.delete(mapeo)
        await self.db.flush()
        return True

    async def _buscar_existente(
        self,
        casilla_id: UUID,
        tenant_id: UUID | None,
        empresa_id: UUID | None,
        exclude_id: UUID | None = None,
    ) -> MapeoCasillaCuenta | None:
        """Busca mapeo existente respetando NULL con .is_()"""
        query = select(MapeoCasillaCuenta).where(
            MapeoCasillaCuenta.casilla_id == casilla_id,
            MapeoCasillaCuenta.tenant_id.is_(tenant_id),
            MapeoCasillaCuenta.empresa_id.is_(empresa_id),
        )
        if exclude_id is not None:
            query = query.where(MapeoCasillaCuenta.id != exclude_id)

        result = await self.db.execute(query)
        return result.scalars().first()

    # ============================================================
    # IMPORT/EXPORT
    # ============================================================
    async def exportar_excel(
        self, tenant_id: UUID | None = None, empresa_id: UUID | None = None
    ) -> BytesIO:
        """Exporta mapeos a Excel"""
        query = (
            select(MapeoCasillaCuenta)
            .options(selectinload(MapeoCasillaCuenta.casilla))
        )
        if tenant_id is not None:
            query = query.where(MapeoCasillaCuenta.tenant_id.is_(tenant_id))
        if empresa_id is not None:
            query = query.where(MapeoCasillaCuenta.empresa_id.is_(empresa_id))

        mapeos = list((await self.db.execute(query)).scalars().all())

        datos = []
        for m in mapeos:
            ambito = "GLOBAL"
            if m.tenant_id is not None and m.empresa_id is not None:
                ambito = "EMPRESA"
            elif m.tenant_id is not None:
                ambito = "TENANT"

            datos.append({
                "casilla_codigo": m.casilla.codigo if m.casilla else "",
                "casilla_nombre": m.casilla.nombre if m.casilla else "",
                "codigo_cuenta_sugerido": m.codigo_cuenta_sugerido,
                "nombre_cuenta_sugerido": m.nombre_cuenta_sugerido,
                "tipo_movimiento": m.tipo_movimiento,
                "ambito": ambito,
            })

        return ExcelHandler.exportar_a_excel(
            datos=datos,
            columnas=COLUMNAS_EXPORT,
            nombre_hoja="Mapeo Contable",
            titulo="Mapeo Casilla SAT → Cuenta Contable",
        )

    async def importar_excel(
        self,
        archivo_bytes: bytes,
        tenant_id: UUID | None = None,
        sobrescribir: bool = False,
    ) -> dict:
        """Importa mapeos desde Excel"""
        try:
            filas = ExcelHandler.importar_desde_excel(
                archivo_bytes=archivo_bytes,
                columnas_requeridas=COLUMNAS_IMPORT_REQUERIDAS,
            )
        except ValueError as e:
            raise ValueError(str(e))

        creados = actualizados = omitidos = 0
        errores: list[str] = []

        for idx, fila in enumerate(filas, 2):
            try:
                codigo_casilla = str(fila.get("codigo_casilla", "")).strip()
                codigo_cuenta = str(fila.get("codigo_cuenta_sugerido", "")).strip()
                nombre_cuenta = str(fila.get("nombre_cuenta_sugerido", "")).strip()
                tipo_mov = str(fila.get("tipo_movimiento", "")).strip().upper()
                ambito = str(fila.get("ambito", "GLOBAL")).strip().upper()

                if not codigo_casilla or not codigo_cuenta or not nombre_cuenta:
                    errores.append(f"Fila {idx}: Campos obligatorios incompletos")
                    continue
                if tipo_mov not in TIPOS_MOVIMIENTO:
                    errores.append(f"Fila {idx}: Movimiento inválido (DEBE/HABER)")
                    continue

                # Buscar casilla
                casilla_query = select(CasillaSat).where(CasillaSat.codigo == codigo_casilla)
                casilla = (await self.db.execute(casilla_query)).scalars().first()
                if casilla is None:
                    errores.append(f"Fila {idx}: Casilla '{codigo_casilla}' no encontrada")
                    continue

                # Determinar ámbito
                t_id = tenant_id if ambito in ("TENANT", "EMPRESA") else None
                e_id = None  # Simplificado: empresa se asigna vía contexto o parámetro futuro

                existente = await self._buscar_existente(casilla.id, t_id, e_id)

                if existente is not None:
                    if sobrescribir:
                        existente.codigo_cuenta_sugerido = codigo_cuenta
                        existente.nombre_cuenta_sugerido = nombre_cuenta
                        existente.tipo_movimiento = tipo_mov
                        actualizados += 1
                    else:
                        omitidos += 1
                else:
                    nuevo = MapeoCasillaCuenta(
                        casilla_id=casilla.id,
                        tenant_id=t_id,
                        empresa_id=e_id,
                        codigo_cuenta_sugerido=codigo_cuenta,
                        nombre_cuenta_sugerido=nombre_cuenta,
                        tipo_movimiento=tipo_mov,
                    )
                    self.db.add(nuevo)
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