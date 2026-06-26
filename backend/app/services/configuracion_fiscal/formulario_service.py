"""Servicio para gestión de formularios SAT con versionado"""

from datetime import date
from uuid import UUID

from app.models.global_models import (
    CasillaSat,
    ExclusionCasilla,
    FormularioSat,
    ReglaFiltradoFactura,
    SeccionFormulario,
)
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class FormularioSatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # QUERIES BÁSICOS
    # ============================================================
    async def obtener_todos(
        self,
        codigo: str | None = None,
        es_version_activa: bool | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[FormularioSat], int]:
        """Lista formularios con filtros y paginación"""
        query = select(FormularioSat)

        if codigo:
            query = query.where(FormularioSat.codigo == codigo)
        if es_version_activa is not None:
            query = query.where(FormularioSat.es_version_activa.is_(es_version_activa))

        # Contar total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Paginar
        query = query.order_by(FormularioSat.codigo, FormularioSat.version.desc())
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        formularios = result.scalars().all()

        return list(formularios), total

    async def obtener_por_id(self, formulario_id: UUID) -> FormularioSat | None:
        """Obtiene un formulario con sus secciones y casillas"""
        query = (
            select(FormularioSat)
            .where(FormularioSat.id == formulario_id)
            .options(
                selectinload(FormularioSat.secciones)
                .selectinload(SeccionFormulario.casillas),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_vigente(
        self, codigo: str, fecha: date | None = None
    ) -> FormularioSat | None:
        """Obtiene la versión vigente de un formulario para una fecha"""
        if fecha is None:
            fecha = date.today()

        query = (
            select(FormularioSat)
            .where(
                FormularioSat.codigo == codigo,
                FormularioSat.es_version_activa.is_(True),
                FormularioSat.fecha_vigencia_desde <= fecha,
                or_(
                    FormularioSat.fecha_vigencia_hasta >= fecha,
                    FormularioSat.fecha_vigencia_hasta.is_(None),
                ),
            )
            .options(
                selectinload(FormularioSat.secciones)
                .selectinload(SeccionFormulario.casillas),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def obtener_historial(self, codigo: str) -> dict:
        """Historial completo de versiones de un formulario"""
        query = (
            select(FormularioSat)
            .where(FormularioSat.codigo == codigo)
            .order_by(FormularioSat.fecha_vigencia_desde.desc())
        )
        result = await self.db.execute(query)
        versiones = result.scalars().all()

        version_actual = await self.obtener_vigente(codigo)

        return {
            "codigo": codigo,
            "versiones": list(versiones),
            "version_actual": version_actual,
            "total_versiones": len(versiones),
        }

    # ============================================================
    # CRUD
    # ============================================================
    async def crear(
        self, data: dict, usuario_id: UUID | None = None
    ) -> FormularioSat:
        """Crea un nuevo formulario con secciones automáticas"""
        formulario = FormularioSat(**data, created_by=usuario_id)
        self.db.add(formulario)
        await self.db.flush()
        
        # ✅ Crear secciones automáticas
        await self._crear_secciones_automaticas(formulario.id, usuario_id)
        
        await self.db.commit()
        
        # Recargar con relaciones
        query = (
            select(FormularioSat)
            .where(FormularioSat.id == formulario.id)
            .options(
                selectinload(FormularioSat.secciones)
                .selectinload(SeccionFormulario.casillas)
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def actualizar(
        self,
        formulario_id: UUID,  # ✅ Cambiar de seccion_id a formulario_id
        data: dict,
        usuario_id: UUID | None = None,
    ) -> FormularioSat | None:  # ✅ Cambiar tipo de retorno
        """Actualiza un formulario"""  # ✅ Actualizar docstring
        formulario = await self.obtener_por_id(formulario_id)  # ✅ Usar formulario
        if formulario is None:
            return None

        for key, value in data.items():
            if hasattr(formulario, key):
                setattr(formulario, key, value)

        formulario.updated_by = usuario_id
        await self.db.commit()
        
        # ✅ Recargar con eager loading de secciones y casillas
        query = (
            select(FormularioSat)  # ✅ Cambiar de SeccionFormulario a FormularioSat
            .where(FormularioSat.id == formulario_id)  # ✅ Usar formulario_id
            .options(
                selectinload(FormularioSat.secciones)
                .selectinload(SeccionFormulario.casillas)
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def eliminar(self, formulario_id: UUID) -> bool:
        """Elimina un formulario (soft delete con cascade)"""
        formulario = await self.obtener_por_id(formulario_id)

        if formulario is None:
            return False

        formulario.es_version_activa = False
        formulario.updated_by = None
        await self.db.commit()
        return True

    # ============================================================
    # VERSIONADO
    # ============================================================
    async def duplicar_version(
        self,
        formulario_id: UUID,
        nueva_version: str,
        fecha_vigencia_desde: date,
        copiar_casillas: bool = True,
        copiar_secciones: bool = True,
        copiar_reglas: bool = True,
        copiar_exclusiones: bool = True,
        usuario_id: UUID | None = None,
    ) -> FormularioSat:
        """Duplica un formulario creando una nueva versión"""
        # Cargar formulario original con todo
        query = (
            select(FormularioSat)
            .where(FormularioSat.id == formulario_id)
            .options(
                selectinload(FormularioSat.secciones)
                .selectinload(SeccionFormulario.casillas)
                .selectinload(CasillaSat.reglas_filtrado),
                selectinload(FormularioSat.secciones)
                .selectinload(SeccionFormulario.casillas)
                .selectinload(CasillaSat.exclusiones),
            )
        )
        result = await self.db.execute(query)
        original = result.scalars().first()

        if original is None:
            raise ValueError(f"Formulario {formulario_id} no encontrado")

        # Crear nueva versión
        nuevo = FormularioSat(
            codigo=original.codigo,
            version=nueva_version,
            nombre=original.nombre,
            descripcion=f"{original.descripcion or ''} - Versión {nueva_version}",
            fecha_vigencia_desde=fecha_vigencia_desde,
            fecha_vigencia_hasta=None,
            es_version_activa=True,
            formulario_padre_id=original.id,
            created_by=usuario_id,
        )
        self.db.add(nuevo)
        await self.db.flush()

        if not copiar_secciones:
            await self.db.refresh(nuevo)
            return nuevo

        # Duplicar secciones y casillas
        mapa_secciones: dict[UUID, SeccionFormulario] = {}
        for seccion_orig in original.secciones:
            nueva_seccion = SeccionFormulario(
                formulario_id=nuevo.id,
                numero_seccion=seccion_orig.numero_seccion,
                titulo=seccion_orig.titulo,
                descripcion=seccion_orig.descripcion,
                orden=seccion_orig.orden,
                tipo_seccion=seccion_orig.tipo_seccion,
                es_obligatoria=seccion_orig.es_obligatoria,
                requiere_exportador=seccion_orig.requiere_exportador,
                created_by=usuario_id,
            )
            self.db.add(nueva_seccion)
            mapa_secciones[seccion_orig.id] = nueva_seccion

        await self.db.flush()

        if not copiar_casillas:
            await self.db.refresh(nuevo)
            return nuevo

        # Duplicar casillas
        mapa_casillas: dict[UUID, CasillaSat] = {}
        for seccion_orig in original.secciones:
            nueva_seccion = mapa_secciones.get(seccion_orig.id)
            if nueva_seccion is None:
                continue

            for casilla_orig in seccion_orig.casillas:
                nueva_casilla = CasillaSat(
                    seccion_id=nueva_seccion.id,
                    codigo=casilla_orig.codigo,
                    codigo_visual=casilla_orig.codigo_visual,
                    nombre=casilla_orig.nombre,
                    descripcion=casilla_orig.descripcion,
                    seccion=casilla_orig.seccion,
                    orden_seccion=casilla_orig.orden_seccion,
                    tipo_casilla=casilla_orig.tipo_casilla,
                    naturaleza=casilla_orig.naturaleza,
                    formula_calculo=casilla_orig.formula_calculo,
                    porcentaje_aplicable=casilla_orig.porcentaje_aplicable,
                    campo_origen_factura=casilla_orig.campo_origen_factura,
                    es_editable=casilla_orig.es_editable,
                    requiere_justificacion=casilla_orig.requiere_justificacion,
                    es_visible_usuario=casilla_orig.es_visible_usuario,
                    created_by=usuario_id,
                )
                self.db.add(nueva_casilla)
                mapa_casillas[casilla_orig.id] = nueva_casilla

        await self.db.flush()

        # Duplicar reglas de filtrado
        if copiar_reglas:
            for casilla_orig_id, nueva_casilla in mapa_casillas.items():
                casilla_orig = next(
                    (
                        c
                        for s in original.secciones
                        for c in s.casillas
                        if c.id == casilla_orig_id
                    ),
                    None,
                )
                if casilla_orig is None:
                    continue

                for regla_orig in casilla_orig.reglas_filtrado:
                    nueva_regla = ReglaFiltradoFactura(
                        casilla_id=nueva_casilla.id,
                        nombre=regla_orig.nombre,
                        descripcion=regla_orig.descripcion,
                        criterios_json=regla_orig.criterios_json,
                        campo_factura=regla_orig.campo_factura,
                        operacion=regla_orig.operacion,
                        orden=regla_orig.orden,
                        es_activa=regla_orig.es_activa,
                        created_by=usuario_id,
                    )
                    self.db.add(nueva_regla)

        # Duplicar exclusiones
        if copiar_exclusiones:
            for casilla_orig_id, nueva_casilla in mapa_casillas.items():
                casilla_orig = next(
                    (
                        c
                        for s in original.secciones
                        for c in s.casillas
                        if c.id == casilla_orig_id
                    ),
                    None,
                )
                if casilla_orig is None:
                    continue

                for exclusion_orig in casilla_orig.exclusiones:
                    nueva_exclusion = ExclusionCasilla(
                        casilla_id=nueva_casilla.id,
                        nombre=exclusion_orig.nombre,
                        descripcion=exclusion_orig.descripcion,
                        criterios_exclusion_json=exclusion_orig.criterios_exclusion_json,
                        es_activa=exclusion_orig.es_activa,
                        created_by=usuario_id,
                    )
                    self.db.add(nueva_exclusion)

        await self.db.refresh(nuevo)
        return nuevo


    async def _crear_secciones_automaticas(
        self, 
        formulario_id: UUID, 
        usuario_id: UUID | None = None
    ) -> None:
        """Crea las secciones 1 y 2 automáticas para todos los formularios"""
        
        # Sección 1: NIT DEL CONTRIBUYENTE
        seccion_1 = SeccionFormulario(
            formulario_id=formulario_id,
            numero_seccion="1",
            titulo="NIT DEL CONTRIBUYENTE",
            descripcion="Información de identificación del contribuyente",
            orden=0,
            tipo_seccion="IDENTIFICACION",
            es_obligatoria=True,
            requiere_exportador=False,
            created_by=usuario_id,
        )
        self.db.add(seccion_1)
        await self.db.flush()
        
        # Casilla 1.1: NIT
        casilla_1_1 = CasillaSat(
            seccion_id=seccion_1.id,
            seccion="1",
            codigo="1.1",
            codigo_visual="NIT",
            nombre="NIT DEL CONTRIBUYENTE",
            descripcion="Número de Identificación Tributaria",
            orden_seccion=0,
            tipo_casilla="REFERENCIA",
            naturaleza="MANUAL",
            es_editable=False,  # ✅ No editable
            es_visible_usuario=True,
            requiere_justificacion=False,
            created_by=usuario_id,
        )
        self.db.add(casilla_1_1)
        
        # Casilla 1.2: Nombre/Razón Social (opcional)
        casilla_1_2 = CasillaSat(
            seccion_id=seccion_1.id,
            seccion="1",
            codigo="1.2",
            codigo_visual="NOMBRE",
            nombre="NOMBRE O RAZÓN SOCIAL",
            descripcion="Nombre o razón social del contribuyente",
            orden_seccion=1,
            tipo_casilla="REFERENCIA",
            naturaleza="MANUAL",
            es_editable=False,  # ✅ No editable
            es_visible_usuario=True,
            requiere_justificacion=False,
            created_by=usuario_id,
        )
        self.db.add(casilla_1_2)
        
        # Sección 2: PERÍODO DE IMPOSICIÓN
        seccion_2 = SeccionFormulario(
            formulario_id=formulario_id,
            numero_seccion="2",
            titulo="PERÍODO DE IMPOSICIÓN",
            descripcion="Período de la declaración",
            orden=1,
            tipo_seccion="PERIODO",
            es_obligatoria=True,
            requiere_exportador=False,
            created_by=usuario_id,
        )
        self.db.add(seccion_2)
        await self.db.flush()
        
        # Casilla 2.1: Mes
        casilla_2_1 = CasillaSat(
            seccion_id=seccion_2.id,
            seccion="2",
            codigo="2.1",
            codigo_visual="MES",
            nombre="Mes",
            descripcion="Mes de la declaración",
            orden_seccion=0,
            tipo_casilla="REFERENCIA",
            naturaleza="MANUAL",
            es_editable=False,  # ✅ No editable
            es_visible_usuario=True,
            requiere_justificacion=False,
            created_by=usuario_id,
        )
        self.db.add(casilla_2_1)
        
        # Casilla 2.2: Año
        casilla_2_2 = CasillaSat(
            seccion_id=seccion_2.id,
            seccion="2",
            codigo="2.2",
            codigo_visual="AÑO",
            nombre="Año",
            descripcion="Año de la declaración",
            orden_seccion=1,
            tipo_casilla="REFERENCIA",
            naturaleza="MANUAL",
            es_editable=False,  # ✅ No editable
            es_visible_usuario=True,
            requiere_justificacion=False,
            created_by=usuario_id,
        )
        self.db.add(casilla_2_2)
        
        await self.db.flush()