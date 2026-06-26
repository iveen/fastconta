"""Servicio para gestión de Casillas SAT"""
from uuid import UUID

from app.models.global_models import (
    CasillaSat,
    ExclusionCasilla,
    ReglaFiltradoFactura,
    SeccionFormulario,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class CasillaSatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_por_seccion(
        self,
        seccion_id: UUID,
        skip: int = 0,
        limit: int = 200,
    ) -> tuple[list[CasillaSat], int]:
        """Lista casillas de una sección"""
        query = (
            select(CasillaSat)
            .where(CasillaSat.seccion_id == seccion_id)
            .options(
                selectinload(CasillaSat.seccion_rel),
                selectinload(CasillaSat.reglas_filtrado),
                selectinload(CasillaSat.exclusiones),
            )
            .order_by(CasillaSat.orden_seccion)
        )

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        casillas = result.scalars().all()

        return list(casillas), total

    async def obtener_por_id(self, casilla_id: UUID) -> CasillaSat | None:
        """Obtiene una casilla con reglas y exclusiones"""
        query = (
            select(CasillaSat)
            .where(CasillaSat.id == casilla_id)
            .options(
                selectinload(CasillaSat.seccion_rel),
                selectinload(CasillaSat.reglas_filtrado),
                selectinload(CasillaSat.exclusiones),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def verificar_editable(self, seccion_id: UUID) -> None:
        """Verifica que el formulario de la sección permite modificaciones"""
        query = (
            select(SeccionFormulario)
            .where(SeccionFormulario.id == seccion_id)
            .options(selectinload(SeccionFormulario.formulario))
        )
        result = await self.db.execute(query)
        seccion = result.scalars().first()
        if seccion is None:
            raise ValueError("Sección no encontrada")
        if seccion.formulario and not seccion.formulario.editable:
            raise ValueError("El formulario está bloqueado y no permite modificaciones")

    # ============================================================
    # CRUD
    # ============================================================
    async def crear(
        self, data: dict, usuario_id: UUID | None = None
    ) -> CasillaSat:
        """Crea una nueva casilla"""
        # Validar que la sección existe
        sec_query = select(SeccionFormulario).where(
            SeccionFormulario.id == data["seccion_id"]
        )
        sec_result = await self.db.execute(sec_query)
        if sec_result.scalars().first() is None:
            raise ValueError("Sección no encontrada")
        
        data["seccion"] = sec_result.numero_seccion

        casilla = CasillaSat(**data, created_by=usuario_id)
        self.db.add(casilla)
        await self.db.commit()  # ✅ Commit en lugar de flush
        
        # ✅ Recargar con eager loading
        query = (
            select(CasillaSat)
            .where(CasillaSat.id == casilla.id)
            .options(
                selectinload(CasillaSat.seccion_rel),
                selectinload(CasillaSat.reglas_filtrado),
                selectinload(CasillaSat.exclusiones),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def actualizar(
        self,
        casilla_id: UUID,
        data: dict,
        usuario_id: UUID | None = None,
    ) -> CasillaSat | None:
        """Actualiza una casilla"""
        casilla = await self.obtener_por_id(casilla_id)
        if casilla is None:
            return None

        for key, value in data.items():
            if hasattr(casilla, key):
                setattr(casilla, key, value)

        casilla.updated_by = usuario_id
        await self.db.commit()  # ✅ Commit en lugar de flush
        
        # ✅ Recargar con eager loading
        query = (
            select(CasillaSat)
            .where(CasillaSat.id == casilla_id)
            .options(
                selectinload(CasillaSat.seccion_rel),
                selectinload(CasillaSat.reglas_filtrado),
                selectinload(CasillaSat.exclusiones),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def eliminar(self, casilla_id: UUID) -> bool:
        """Elimina una casilla (hard delete con cascade)"""
        casilla = await self.obtener_por_id(casilla_id)
        if casilla is None:
            return False

        await self.db.delete(casilla)
        await self.db.commit()  # ✅ Commit en lugar de flush
        return True

    # ============================================================
    # DUPLICAR
    # ============================================================
    async def duplicar(
        self,
        casilla_id: UUID,
        nuevo_codigo: str,
        nuevo_nombre: str | None = None,
        copiar_reglas: bool = True,
        copiar_exclusiones: bool = True,
        usuario_id: UUID | None = None,
    ) -> CasillaSat:
        """Duplica una casilla con sus reglas y exclusiones"""
        original = await self.obtener_por_id(casilla_id)
        if original is None:
            raise ValueError("Casilla no encontrada")

        nueva = CasillaSat(
            seccion_id=original.seccion_id,
            codigo=nuevo_codigo,
            codigo_visual=original.codigo_visual,
            nombre=nuevo_nombre or f"{original.nombre} (copia)",
            descripcion=original.descripcion,
            orden_seccion=original.orden_seccion + 1,
            tipo_casilla=original.tipo_casilla,
            naturaleza=original.naturaleza,
            formula_calculo=original.formula_calculo,
            porcentaje_aplicable=original.porcentaje_aplicable,
            campo_origen_factura=original.campo_origen_factura,
            es_editable=original.es_editable,
            requiere_justificacion=original.requiere_justificacion,
            es_visible_usuario=original.es_visible_usuario,
            dependencias=original.dependencias,
            funcion_calculo=original.funcion_calculo,
            parametros_funcion=original.parametros_funcion,
            created_by=usuario_id,
        )
        self.db.add(nueva)
        await self.db.commit()  # ✅ Commit en lugar de flush

        # Duplicar reglas
        if copiar_reglas:
            for regla in original.reglas_filtrado:
                nueva_regla = ReglaFiltradoFactura(
                    casilla_id=nueva.id,
                    nombre=regla.nombre,
                    descripcion=regla.descripcion,
                    criterios_json=regla.criterios_json,
                    campo_factura=regla.campo_factura,
                    operacion=regla.operacion,
                    orden=regla.orden,
                    es_activa=regla.es_activa,
                    created_by=usuario_id,
                )
                self.db.add(nueva_regla)

        # Duplicar exclusiones
        if copiar_exclusiones:
            for exclusion in original.exclusiones:
                nueva_exclusion = ExclusionCasilla(
                    casilla_id=nueva.id,
                    nombre=exclusion.nombre,
                    descripcion=exclusion.descripcion,
                    criterios_exclusion_json=exclusion.criterios_exclusion_json,
                    es_activa=exclusion.es_activa,
                    created_by=usuario_id,
                )
                self.db.add(nueva_exclusion)

        await self.db.commit()  # ✅ Commit final
        
        # ✅ Recargar con eager loading
        query = (
            select(CasillaSat)
            .where(CasillaSat.id == nueva.id)
            .options(
                selectinload(CasillaSat.seccion_rel),
                selectinload(CasillaSat.reglas_filtrado),
                selectinload(CasillaSat.exclusiones),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()