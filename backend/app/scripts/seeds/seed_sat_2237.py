"""
Script para poblar el Formulario SAT-2237 (IVA General).
Idempotente: seguro de ejecutar múltiples veces. Actualiza si existe, crea si no.
Ejecutar: python -m app.scripts.seeds.seed_sat_2237
"""
import asyncio
import os
import sys
from datetime import date

from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import AsyncSessionLocal
from app.models.global_models import (
    CasillaSat,
    ExclusionCasilla,
    FormularioSat,
    RegimenFiscal,
    RegimenFormularioSat,
    ReglaFiltradoFactura,
    SeccionFormulario,
)
from app.scripts.data.sat_2237 import (
    CASILLAS_SAT_2237,
    EXCLUSIONES_SAT_2237,
    FORMULARIO_SAT_2237,
    REGIMENES_ASOCIADOS,
    REGLAS_FILTRADO_SAT_2237,
    SECCIONES_SAT_2237,
)


async def seed():
    print("=" * 70)
    print(" INICIANDO CARGA DEL FORMULARIO SAT-2237 (v2.0 ACTIVA) ")
    print("=" * 70)
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. UPSERT FORMULARIO
            stmt = select(FormularioSat).where(
                FormularioSat.codigo == FORMULARIO_SAT_2237["codigo"],
                FormularioSat.version == FORMULARIO_SAT_2237["version"]
            )
            result = await db.execute(stmt)
            formulario = result.scalar_one_or_none()
            
            if formulario:
                for k, v in FORMULARIO_SAT_2237.items():
                    setattr(formulario, k, v)
                print(f"  ✅ Formulario actualizado: {formulario.codigo} v{formulario.version}")
            else:
                formulario = FormularioSat(
                    **FORMULARIO_SAT_2237,
                    fecha_vigencia_desde=date(2026, 1, 1),
                    fecha_vigencia_hasta=None,
                    created_by=None
                )
                db.add(formulario)
                print(f"  ➕ Formulario creado: {formulario.codigo} v{formulario.version}")
            
            await db.flush() # Obtener formulario.id

            # 2. UPSERT SECCIONES
            secciones_map = {} # {numero_seccion: id}
            for sec_data in SECCIONES_SAT_2237:
                stmt = select(SeccionFormulario).where(
                    SeccionFormulario.formulario_id == formulario.id,
                    SeccionFormulario.numero_seccion == sec_data["numero_seccion"]
                )
                result = await db.execute(stmt)
                seccion = result.scalar_one_or_none()
                
                if seccion:
                    for k, v in sec_data.items():
                        setattr(seccion, k, v)
                else:
                    seccion = SeccionFormulario(formulario_id=formulario.id, **sec_data, created_by=None)
                    db.add(seccion)
                await db.flush()
                secciones_map[sec_data["numero_seccion"]] = seccion.id
            print(f"  ✅ {len(SECCIONES_SAT_2237)} secciones procesadas.")

            # 3. UPSERT CASILLAS
            casillas_creadas = 0
            for cas_data in CASILLAS_SAT_2237:
                seccion_id = secciones_map.get(cas_data["seccion"])
                if not seccion_id:
                    print(f"  ⚠️  Skip casilla {cas_data['codigo']}: Sección {cas_data['seccion']} no encontrada")
                    continue
                
                stmt = select(CasillaSat).where(
                    CasillaSat.seccion_id == seccion_id,
                    CasillaSat.codigo == cas_data["codigo"]
                )
                result = await db.execute(stmt)
                casilla = result.scalar_one_or_none()
                
                # Preparar datos (quitamos 'seccion' porque no es columna, usamos seccion_id)
                cas_data_db = {k: v for k, v in cas_data.items() if k != "seccion"}
                cas_data_db["seccion_id"] = seccion_id
                
                if casilla:
                    for k, v in cas_data_db.items():
                        setattr(casilla, k, v)
                else:
                    casilla = CasillaSat(**cas_data_db, created_by=None)
                    db.add(casilla)
                    casillas_creadas += 1
            print(f"  ✅ {len(CASILLAS_SAT_2237)} casillas procesadas ({casillas_creadas} nuevas).")
            await db.flush()

            # 4. UPSERT REGLAS DE FILTRADO
            # (Primero necesitamos un mapa de codigo_casilla -> casilla_id)
            stmt_casillas = select(CasillaSat.codigo, CasillaSat.id).where(CasillaSat.seccion_id.in_(list(secciones_map.values())))
            casillas_result = await db.execute(stmt_casillas)
            casillas_id_map = {row.codigo: row.id for row in casillas_result.all()}

            for regla_data in REGLAS_FILTRADO_SAT_2237:
                casilla_id = casillas_id_map.get(regla_data["casilla_codigo"])
                if not casilla_id:
                    continue
                
                # Para reglas, usamos una combinación única ficticia o verificamos existencia
                stmt = select(ReglaFiltradoFactura).where(
                    ReglaFiltradoFactura.casilla_id == casilla_id,
                    ReglaFiltradoFactura.nombre == regla_data["nombre"]
                )
                result = await db.execute(stmt)
                regla = result.scalar_one_or_none()
                
                regla_data_db = {k: v for k, v in regla_data.items() if k != "casilla_codigo"}
                regla_data_db["casilla_id"] = casilla_id
                
                if regla:
                    for k, v in regla_data_db.items():
                        setattr(regla, k, v)
                else:
                    regla = ReglaFiltradoFactura(**regla_data_db, created_by=None)
                    db.add(regla)
            print(f"  ✅ {len(REGLAS_FILTRADO_SAT_2237)} reglas de filtrado procesadas.")

            # 5. UPSERT EXCLUSIONES
            for exc_data in EXCLUSIONES_SAT_2237:
                casilla_id = casillas_id_map.get(exc_data["casilla_codigo"])
                if not casilla_id:
                    continue
                
                stmt = select(ExclusionCasilla).where(
                    ExclusionCasilla.casilla_id == casilla_id,
                    ExclusionCasilla.nombre == exc_data["nombre"]
                )
                result = await db.execute(stmt)
                exclusion = result.scalar_one_or_none()
                
                exc_data_db = {k: v for k, v in exc_data.items() if k != "casilla_codigo"}
                exc_data_db["casilla_id"] = casilla_id
                
                if exclusion:
                    for k, v in exc_data_db.items():
                        setattr(exclusion, k, v)
                else:
                    exclusion = ExclusionCasilla(**exc_data_db, created_by=None)
                    db.add(exclusion)
            print(f"  ✅ {len(EXCLUSIONES_SAT_2237)} exclusiones procesadas.")

            # 6. ASOCIAR CON REGÍMENES
            stmt_regimenes = select(RegimenFiscal.codigo, RegimenFiscal.id)
            regimenes_map = {row.codigo: row.id for row in (await db.execute(stmt_regimenes)).all()}
            
            for reg_codigo in REGIMENES_ASOCIADOS:
                regimen_id = regimenes_map.get(reg_codigo)
                if not regimen_id:
                    print(f"  ⚠️  Régimen no encontrado: {reg_codigo}")
                    continue
                
                stmt = select(RegimenFormularioSat).where(
                    RegimenFormularioSat.regimen_id == regimen_id,
                    RegimenFormularioSat.formulario_id == formulario.id
                )
                result = await db.execute(stmt)
                asociacion = result.scalar_one_or_none()
                
                if not asociacion:
                    nueva_asociacion = RegimenFormularioSat(
                        regimen_id=regimen_id,
                        formulario_id=formulario.id,
                        es_obligatorio=True,
                        created_by=None
                    )
                    db.add(nueva_asociacion)
            print(f"  ✅ Formulario asociado a {len(REGIMENES_ASOCIADOS)} regímenes.")

            # COMMIT FINAL
            await db.commit()
            print("\n" + "=" * 70)
            print("✅ CARGA DEL SAT-2237 COMPLETADA EXITOSAMENTE")
            print("=" * 70)
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error durante el seed: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed())