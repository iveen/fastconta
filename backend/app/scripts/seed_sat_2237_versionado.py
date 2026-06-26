"""
Seed del Formulario SAT-2237 con versionado.
Crea:
- Versión 1.0 (2025): Basado en formulario presentado abril 2025
- Versión 2.0 (2026): Basado en formulario actual con secciones 9.1 y 9.2 separadas
"""

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.global_models import CasillaSat, FormularioSat, SeccionFormulario
from app.services.formulario_service import FormularioService


def seed_sat_2237_versionado(db: Session):
    """
    Crea el SAT-2237 con dos versiones:
    - v1.0: Vigente desde 2025-01-01 (formulario 2025)
    - v2.0: Vigente desde 2026-01-01 (formulario 2026 con mejoras)
    """
    
    service = FormularioService(db)
    
    # =========================================================================
    # VERSIÓN 1.0 (2025) - Formulario base
    # =========================================================================
    print("Creando SAT-2237 v1.0 (2025)...")
    
    formulario_v1 = FormularioSat(
        id=uuid.uuid4(),
        codigo='SAT-2237',
        version='1.0',
        nombre='Declaración Jurativa Mensual del IVA - Régimen General',
        descripcion='Formulario 2025. Contribuyentes del Régimen General.',
        fecha_vigencia_desde=date(2025, 1, 1),
        fecha_vigencia_hasta=date(2025, 12, 31),
        es_version_activa=False,
        created_by=None
    )
    db.add(formulario_v1)
    db.flush()
    
    # Crear secciones básicas (simplificado para el ejemplo)
    secciones_v1 = [
        {'numero': '3', 'titulo': 'Débito Fiscal por Operaciones Locales', 'tipo': 'DEBITO_FISCAL', 'orden': 3},
        {'numero': '4', 'titulo': 'Operaciones de Exportación y Transferencia', 'tipo': 'EXPORTACIONES', 'orden': 4},
        {'numero': '5', 'titulo': 'Crédito Fiscal por Operaciones Locales', 'tipo': 'CREDITO_FISCAL', 'orden': 5},
        {'numero': '7', 'titulo': 'Determinación del Impuesto', 'tipo': 'DETERMINACION', 'orden': 7},
        {'numero': '9', 'titulo': 'Monto de Operaciones Realizadas', 'tipo': 'INFORMATIVA', 'orden': 9},
    ]
    
    for sec_data in secciones_v1:
        seccion = SeccionFormulario(
            id=uuid.uuid4(),
            formulario_id=formulario_v1.id,
            numero_seccion=sec_data['numero'],
            titulo=sec_data['titulo'],
            orden=sec_data['orden'],
            tipo_seccion=sec_data['tipo'],
            es_obligatoria=True,
            created_by=None
        )
        db.add(seccion)
    
    db.flush()
    print(f"✅ SAT-2237 v1.0 creado: {formulario_v1.id}")
    
    # =========================================================================
    # VERSIÓN 2.0 (2026) - Duplicar desde v1.0 y mejorar
    # =========================================================================
    print("\nCreando SAT-2237 v2.0 (2026) desde v1.0...")
    
    formulario_v2 = service.duplicar_formulario_nueva_version(
        formulario_id=formulario_v1.id,
        nueva_version='2.0',
        fecha_vigencia_desde=date(2026, 1, 1),
        usuario_id=None
    )
    
    # Ahora agregamos las mejoras de la v2.0:
    # Sección 9 dividida en 9.1 y 9.2
    
    # Agregar sección 9.1 (nueva en 2026)
    seccion_9_1 = SeccionFormulario(
        id=uuid.uuid4(),
        formulario_id=formulario_v2.id,
        numero_seccion='9.1',
        titulo='Cantidad de Operaciones Realizadas',
        descripcion='Conteo de documentos emitidos y recibidos',
        orden=9,
        tipo_seccion='INFORMATIVA',
        es_obligatoria=True,
        created_by=None
    )
    db.add(seccion_9_1)
    
    # Casillas para 9.1
    casillas_9_1 = [
        {'codigo': '9.1.1', 'nombre': 'Facturas (incluidas anuladas) - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.2', 'nombre': 'Facturas (incluidas anuladas) - Recibidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.3', 'nombre': 'FYDUCA - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.4', 'nombre': 'FYDUCA - Recibidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.5', 'nombre': 'Constancias de exención - Emitidas', 'tipo': 'CONTEO'},
        {'codigo': '9.1.6', 'nombre': 'Constancias de exención - Recibidas', 'tipo': 'CONTEO'},
    ]
    
    for i, cas_data in enumerate(casillas_9_1, 1):
        casilla = CasillaSat(
            id=uuid.uuid4(),
            formulario_id=formulario_v2.id,
            seccion_id=seccion_9_1.id,
            codigo=cas_data['codigo'],
            codigo_visual=f'9.1.{i}',
            nombre=cas_data['nombre'],
            seccion='9.1',
            orden_seccion=i,
            tipo_casilla=cas_data['tipo'],
            created_by=None
        )
        db.add(casilla)
    
    # Agregar sección 9.2 (nueva en 2026)
    seccion_9_2 = SeccionFormulario(
        id=uuid.uuid4(),
        formulario_id=formulario_v2.id,
        numero_seccion='9.2',
        titulo='Monto de Operaciones Realizadas',
        descripcion='Valores monetarios de notas de crédito y débito',
        orden=9,
        tipo_seccion='INFORMATIVA',
        es_obligatoria=True,
        created_by=None
    )
    db.add(seccion_9_2)
    
    # Casillas para 9.2
    casillas_9_2 = [
        {'codigo': '9.2.1', 'nombre': 'Valor de las notas de crédito del período - Emitidas', 'tipo': 'REFERENCIA'},
        {'codigo': '9.2.2', 'nombre': 'Valor de las notas de crédito del período - Recibidas', 'tipo': 'REFERENCIA'},
        {'codigo': '9.2.3', 'nombre': 'Valor de las notas de débito del período - Emitidas', 'tipo': 'REFERENCIA'},
        {'codigo': '9.2.4', 'nombre': 'Valor de las notas de débito del período - Recibidas', 'tipo': 'REFERENCIA'},
    ]
    
    for i, cas_data in enumerate(casillas_9_2, 1):
        casilla = CasillaSat(
            id=uuid.uuid4(),
            formulario_id=formulario_v2.id,
            seccion_id=seccion_9_2.id,
            codigo=cas_data['codigo'],
            codigo_visual=f'9.2.{i}',
            nombre=cas_data['nombre'],
            seccion='9.2',
            orden_seccion=i,
            tipo_casilla=cas_data['tipo'],
            created_by=None
        )
        db.add(casilla)
    
    db.commit()
    print(f"✅ SAT-2237 v2.0 creado: {formulario_v2.id}")
    
    # =========================================================================
    # RESUMEN
    # =========================================================================
    print("\n" + "="*70)
    print("✅ SEED SAT-2237 VERSIONADO COMPLETADO")
    print("="*70)
    print(f"Versión 1.0 (2025): {formulario_v1.id}")
    print("  - Vigencia: 2025-01-01 a 2025-12-31")
    print("  - Estado: Inactiva")
    print(f"\nVersión 2.0 (2026): {formulario_v2.id}")
    print("  - Vigencia: 2026-01-01 a presente")
    print("  - Estado: Activa")
    print("  - Basada en: v1.0")
    print("  - Mejoras: Secciones 9.1 y 9.2 separadas")
    print("="*70)
    
    return formulario_v1, formulario_v2


if __name__ == "__main__":
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        seed_sat_2237_versionado(db)
        print("\n🎉 Seed versionado ejecutado correctamente")
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()