"""
Servicio para gestión de formularios SAT con versionado.
Permite duplicar formularios, mantener histórico y obtener versiones vigentes.
"""

import uuid
from datetime import date
from typing import List, Optional

from app.models.global_models import (
    CasillaSat,
    ExclusionCasilla,
    FormularioSat,
    ReglaFiltradoFactura,
    SeccionFormulario,
)
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload


class FormularioService:
    """
    Servicio para gestión de formularios SAT con versionado.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def obtener_formulario_vigente(self, codigo: str, fecha: date = None) -> Optional[FormularioSat]:
        """
        Obtiene la versión vigente de un formulario para una fecha específica.
        
        Args:
            codigo: Código del formulario (ej: 'SAT-2237')
            fecha: Fecha de vigencia (default: hoy)
        
        Returns:
            FormularioSat o None si no existe versión vigente
        """
        if fecha is None:
            fecha = date.today()
        
        return self.db.query(FormularioSat).filter(
            FormularioSat.codigo == codigo,
            FormularioSat.es_version_activa.is_(True),
            FormularioSat.fecha_vigencia_desde <= fecha,
            or_(
                FormularioSat.fecha_vigencia_hasta >= fecha,
                FormularioSat.fecha_vigencia_hasta.is_(None)
            )
        ).options(
            joinedload(FormularioSat.secciones),
            joinedload(FormularioSat.casillas)
        ).first()
    
    def obtener_todas_versiones(self, codigo: str) -> List[FormularioSat]:
        """
        Obtiene todas las versiones de un formulario ordenadas por fecha.
        """
        return self.db.query(FormularioSat).filter(
            FormularioSat.codigo == codigo
        ).order_by(
            FormularioSat.fecha_vigencia_desde.desc()
        ).all()
    
    def duplicar_formulario_nueva_version(
        self, 
        formulario_id: uuid.UUID, 
        nueva_version: str,
        fecha_vigencia_desde: date,
        usuario_id: Optional[uuid.UUID] = None
    ) -> FormularioSat:
        """
        Duplica un formulario existente creando una nueva versión.
        Copia todas las secciones y casillas manteniendo la estructura.
        
        Args:
            formulario_id: ID del formulario base
            nueva_version: Número de versión (ej: '2.0')
            fecha_vigencia_desde: Fecha de inicio de vigencia
            usuario_id: Usuario que crea la versión (para auditoría)
        
        Returns:
            Nuevo formulario creado
        """
        # Obtener formulario original
        formulario_original = self.db.query(FormularioSat).filter(
            FormularioSat.id == formulario_id
        ).options(
            joinedload(FormularioSat.secciones).joinedload(SeccionFormulario.casillas),
            joinedload(FormularioSat.casillas).joinedload(CasillaSat.reglas_filtrado),
            joinedload(FormularioSat.casillas).joinedload(CasillaSat.exclusiones)
        ).first()
        
        if not formulario_original:
            raise ValueError(f"Formulario con ID {formulario_id} no encontrado")
        
        # Desactivar versión anterior (opcional, configurable)
        # formulario_original.es_version_activa = False
        # formulario_original.fecha_vigencia_hasta = fecha_vigencia_desde - timedelta(days=1)
        
        # Crear nueva versión
        nuevo_formulario = FormularioSat(
            id=uuid.uuid4(),
            codigo=formulario_original.codigo,
            version=nueva_version,
            nombre=formulario_original.nombre,
            descripcion=f"{formulario_original.descripcion or ''} - Versión {nueva_version}",
            fecha_vigencia_desde=fecha_vigencia_desde,
            fecha_vigencia_hasta=None,
            es_version_activa=True,
            formulario_padre_id=formulario_original.id,
            created_by=usuario_id
        )
        
        self.db.add(nuevo_formulario)
        self.db.flush()  # Para obtener el ID
        
        # Diccionario para mapear IDs originales a nuevos IDs
        mapa_secciones = {}
        mapa_casillas = {}
        
        # Duplicar secciones
        for seccion_orig in formulario_original.secciones:
            nueva_seccion = SeccionFormulario(
                id=uuid.uuid4(),
                formulario_id=nuevo_formulario.id,
                numero_seccion=seccion_orig.numero_seccion,
                titulo=seccion_orig.titulo,
                descripcion=seccion_orig.descripcion,
                orden=seccion_orig.orden,
                tipo_seccion=seccion_orig.tipo_seccion,
                es_obligatoria=seccion_orig.es_obligatoria,
                requiere_exportador=seccion_orig.requiere_exportador,
                created_by=usuario_id
            )
            self.db.add(nueva_seccion)
            mapa_secciones[seccion_orig.id] = nueva_seccion
        
        self.db.flush()
        
        # Duplicar casillas
        for casilla_orig in formulario_original.casillas:
            nueva_casilla = CasillaSat(
                id=uuid.uuid4(),
                formulario_id=nuevo_formulario.id,
                seccion_id=mapa_secciones.get(casilla_orig.seccion_id),
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
                created_by=usuario_id
            )
            self.db.add(nueva_casilla)
            mapa_casillas[casilla_orig.id] = nueva_casilla
        
        self.db.flush()
        
        # Duplicar reglas de filtrado
        for casilla_orig in formulario_original.casillas:
            if casilla_orig.id in mapa_casillas:
                nueva_casilla = mapa_casillas[casilla_orig.id]
                
                for regla_orig in casilla_orig.reglas_filtrado:
                    nueva_regla = ReglaFiltradoFactura(
                        id=uuid.uuid4(),
                        casilla_id=nueva_casilla.id,
                        nombre=regla_orig.nombre,
                        descripcion=regla_orig.descripcion,
                        criterios_json=regla_orig.criterios_json,  # JSONB se copia directo
                        campo_factura=regla_orig.campo_factura,
                        operacion=regla_orig.operacion,
                        orden=regla_orig.orden,
                        es_activa=regla_orig.es_activa,
                        created_by=usuario_id
                    )
                    self.db.add(nueva_regla)
        
        # Duplicar exclusiones
        for casilla_orig in formulario_original.casillas:
            if casilla_orig.id in mapa_casillas:
                nueva_casilla = mapa_casillas[casilla_orig.id]
                
                for exclusion_orig in casilla_orig.exclusiones:
                    nueva_exclusion = ExclusionCasilla(
                        id=uuid.uuid4(),
                        casilla_id=nueva_casilla.id,
                        nombre=exclusion_orig.nombre,
                        descripcion=exclusion_orig.descripcion,
                        criterios_exclusion_json=exclusion_orig.criterios_exclusion_json,
                        es_activa=exclusion_orig.es_activa,
                        created_by=usuario_id
                    )
                    self.db.add(nueva_exclusion)
        
        self.db.commit()
        self.db.refresh(nuevo_formulario)
        
        return nuevo_formulario
    
    def obtener_historial_versiones(self, codigo: str) -> dict:
        """
        Obtiene el historial completo de versiones de un formulario.
        
        Returns:
            Diccionario con:
            - versiones: Lista de versiones
            - version_actual: Versión vigente
            - total_versiones: Cantidad total
        """
        versiones = self.obtener_todas_versiones(codigo)
        version_actual = self.obtener_formulario_vigente(codigo)
        
        return {
            "codigo": codigo,
            "versiones": [
                {
                    "id": v.id,
                    "version": v.version,
                    "nombre": v.nombre,
                    "fecha_vigencia_desde": v.fecha_vigencia_desde,
                    "fecha_vigencia_hasta": v.fecha_vigencia_hasta,
                    "es_acti va": v.es_version_activa,
                    "tiene_padre": v.formulario_padre_id is not None
                }
                for v in versiones
            ],
            "version_actual": {
                "id": version_actual.id,
                "version": version_actual.version,
                "fecha_vigencia_desde": version_actual.fecha_vigencia_desde
            } if version_actual else None,
            "total_versiones": len(versiones)
        }