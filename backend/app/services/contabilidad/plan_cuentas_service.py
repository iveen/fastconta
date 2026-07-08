# app/services/plan_cuentas_service.py
import io

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def procesar_importacion_excel(
    file: UploadFile,
    empresa_id: int,  # ✅ BIGINT (era UUID)
    db: AsyncSession,
    schema_name: str
) -> dict:
    """
    Importa plan de cuentas desde Excel.
    ⚠️ CRÍTICO: No generar IDs con uuid4(), dejar que la BD genere BIGINT autoincremental.
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .xlsx o .xls")
    
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        required_cols = ['codigo', 'nombre', 'tipo', 'naturaleza', 'nivel']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=400, 
                detail=f"Columnas requeridas faltantes: {required_cols}"
            )
        
        df['codigo'] = df['codigo'].astype(str).str.strip()
        df['nivel'] = df['nivel'].astype(int)
        df = df.sort_values(by='nivel').reset_index(drop=True)
        
        # ✅ CORREGIDO: Query con is_active en lugar de activa
        existentes_sql = text(f"""
            SELECT id, codigo FROM {schema_name}.plan_cuentas 
            WHERE empresa_id = :empresa_id AND is_active = true
        """)
        result = await db.execute(existentes_sql, {"empresa_id": empresa_id})  # ✅ int (no str)
        codigo_a_id = {row.codigo: row.id for row in result.all()}
        
        cuentas_a_insertar = []
        errores = []
        
        for index, row in df.iterrows():
            codigo = str(row['codigo'])
            
            if codigo in codigo_a_id:
                errores.append(f"Fila {index + 2}: El código '{codigo}' ya existe en esta empresa.")
                continue
            
            tipo_val = str(row['tipo']).strip().lower()
            naturaleza_val = str(row['naturaleza']).strip().lower()
            
            if tipo_val not in ["activo", "pasivo", "patrimonio", "ingreso", "gasto"]:
                errores.append(f"Fila {index + 2}: Tipo '{row['tipo']}' no válido.")
                continue
            
            if naturaleza_val not in ["deudora", "acreedora"]:
                errores.append(f"Fila {index + 2}: Naturaleza '{row['naturaleza']}' no válida.")
                continue
            
            cuenta_padre_id = None
            if pd.notna(row.get('cuenta_padre_codigo')):
                padre_codigo = str(row['cuenta_padre_codigo']).strip()
                if padre_codigo in codigo_a_id:
                    cuenta_padre_id = codigo_a_id[padre_codigo]
                else:
                    errores.append(f"Fila {index + 2}: Cuenta padre '{padre_codigo}' no encontrada.")
                    continue
            
            # ✅ CORREGIDO: NO generar ID, dejar que la BD lo haga (RETURNING id)
            cuentas_a_insertar.append({
                "codigo": codigo,
                "nombre": str(row['nombre']).strip(),
                "tipo": tipo_val,
                "naturaleza": naturaleza_val,
                "nivel": int(row['nivel']),
                "acepta_tercero": bool(row.get('acepta_tercero', False)),
                "cuenta_padre_id": cuenta_padre_id,  # ✅ int (no str)
                "empresa_id": empresa_id  # ✅ int (no str)
            })
            codigo_a_id[codigo] = None  # Placeholder para evitar duplicados en el loop
        
        if errores:
            raise HTTPException(
                status_code=400, 
                detail={"mensaje": "Errores de validación en el archivo", "errores": errores}
            )
        
        if not cuentas_a_insertar:
            raise HTTPException(status_code=400, detail="No hay cuentas válidas para importar.")
        
        # ✅ CORREGIDO: INSERT sin ID, usar RETURNING para obtener los IDs generados
        insert_sql = text(f"""
            INSERT INTO {schema_name}.plan_cuentas 
            (codigo, nombre, tipo, naturaleza, acepta_tercero, nivel, cuenta_padre_id, empresa_id, is_active, created_at)
            VALUES 
            (:codigo, :nombre, :tipo, :naturaleza, :acepta_tercero, :nivel, :cuenta_padre_id, :empresa_id, true, NOW())
            RETURNING id, codigo
        """)
        
        ids_generados = []
        for cuenta in cuentas_a_insertar:
            result = await db.execute(insert_sql, cuenta)
            row = result.first()
            if row:
                ids_generados.append(row.id)
                # Actualizar el mapeo para cuentas hijas
                codigo_a_id[cuenta["codigo"]] = row.id
        
        await db.commit()
        
        return {
            "mensaje": f"Importación exitosa. {len(cuentas_a_insertar)} cuentas creadas.",
            "ids_creados": ids_generados
        }
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al procesar el archivo: {str(e)}")


async def exportar_plan_cuentas(empresa_id: int, db: AsyncSession, schema_name: str) -> io.BytesIO:  # ✅ BIGINT
    """
    Consulta las cuentas activas de una empresa y genera un buffer de Excel en memoria.
    """
    # ✅ CORREGIDO: is_active en lugar de activa
    sql = text(f"""
        SELECT c.codigo, c.nombre, c.tipo, c.naturaleza, c.nivel, c.acepta_tercero,
        (SELECT p.codigo FROM {schema_name}.plan_cuentas p WHERE p.id = c.cuenta_padre_id) as cuenta_padre_codigo
        FROM {schema_name}.plan_cuentas c
        WHERE c.empresa_id = :empresa_id AND c.is_active = true
        ORDER BY c.codigo
    """)
    
    result = await db.execute(sql, {"empresa_id": empresa_id})  # ✅ int (no str)
    rows = result.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No hay cuentas activas para exportar en esta empresa.")
    
    df = pd.DataFrame(rows, columns=[
        "codigo", "nombre", "tipo", "naturaleza", "nivel", "acepta_tercero", "cuenta_padre_codigo"
    ])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="PlanCuentas")
    
    output.seek(0)
    return output