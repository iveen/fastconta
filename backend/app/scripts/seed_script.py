# app/scripts/seeds/seed_script.py
import asyncio
import sys
from pathlib import Path

# Asegurar imports desde la raíz del proyecto
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession

# 👇 Importar AsyncSessionLocal directamente desde base
from app.db.base import AsyncSessionLocal
from app.models.global_models import CasillaSat, FormularioSat, SeccionFormulario
from app.scripts.seeds.sat_2237_iva import SAT_2237_FORMULARIO


async def seed_formularios_sat(db: AsyncSession):
    print("🌱 Iniciando Seed de Formularios SAT...")
    
    try:
        formulario_data = SAT_2237_FORMULARIO
        
        # 1. Crear Formulario
        formulario = FormularioSat(
            codigo=formulario_data["codigo"],
            version=formulario_data["version"],
            nombre=formulario_data["nombre"],
            descripcion=formulario_data["descripcion"],
            es_version_activa=formulario_data["es_version_activa"],
            editable=formulario_data["editable"]
        )
        db.add(formulario)
        await db.flush()
        print(f"✅ Formulario creado: {formulario.codigo}")
        
        # 2. Crear Secciones y Casillas
        for sec_data in formulario_data.get("secciones", []):
            seccion = SeccionFormulario(
                formulario_id=formulario.id,
                numero_seccion=sec_data["numero_seccion"],
                titulo=sec_data["titulo"],
                tipo_seccion=sec_data["tipo_seccion"],
                orden=sec_data["orden"],
                es_automatica=sec_data.get("es_automatica", False)
            )
            db.add(seccion)
            await db.flush()
            
            for cas_data in sec_data.get("casillas", []):
                casilla = CasillaSat(
                    seccion_id=seccion.id,
                    codigo=cas_data["codigo"],
                    nombre=cas_data["nombre"],
                    tipo_casilla=cas_data["tipo_casilla"],
                    naturaleza=cas_data.get("naturaleza"),
                    formula_calculo=cas_data.get("formula_calculo"),
                    orden_seccion=cas_data.get("orden_seccion", 0),
                    es_editable=cas_data.get("es_editable", True),
                    es_automatica=cas_data.get("es_automatica", False),
                    dependencias=cas_data.get("dependencias")
                )
                db.add(casilla)
                
        await db.commit()
        print("🎉 Seed completado exitosamente.")
        
    except Exception as e:
        await db.rollback()
        print(f"❌ Error durante el seed: {e}")
        raise
    finally:
        await db.close()


async def main():
    # 👇 Crear sesión manualmente con AsyncSessionLocal
    async with AsyncSessionLocal() as session:
        # Forzar schema public para seeds
        from sqlalchemy import text
        await session.execute(text("SET LOCAL search_path TO public"))
        await session.flush()
        
        await seed_formularios_sat(session)


if __name__ == "__main__":
    asyncio.run(main())