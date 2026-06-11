import io
import uuid
from uuid import UUID

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


# 🔹 NUEVO: Agregar schema_name como parámetro
async def procesar_importacion_excel(
    file: UploadFile, 
    empresa_id: UUID, 
    db: AsyncSession,
    schema_name: str  # 🔹 Parámetro obligatorio
) -> dict:
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos .xlsx o .xls")

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        required_cols = ['codigo', 'nombre', 'tipo', 'naturaleza', 'nivel']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(status_code=400, detail=f"Columnas requeridas faltantes: {required_cols}")

        df['codigo'] = df['codigo'].astype(str).str.strip()
        df['nivel'] = df['nivel'].astype(int)
        df = df.sort_values(by='nivel').reset_index(drop=True)

        # 🔹 Usar schema_name directamente en la consulta
        existentes_sql = text(f"""
            SELECT id, codigo FROM {schema_name}.plan_cuentas 
            WHERE empresa_id = :empresa_id AND activa = true
        """)
        result = await db.execute(existentes_sql, {"empresa_id": str(empresa_id)})
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

            temp_id = uuid.uuid4()
            cuentas_a_insertar.append({
                "id": str(temp_id),
                "codigo": codigo,
                "nombre": str(row['nombre']).strip(),
                "tipo": tipo_val,
                "naturaleza": naturaleza_val,
                "nivel": int(row['nivel']),
                "acepta_tercero": bool(row.get('acepta_tercero', False)),
                "cuenta_padre_id": str(cuenta_padre_id) if cuenta_padre_id else None,
                "empresa_id": str(empresa_id)
            })
            codigo_a_id[codigo] = temp_id

        if errores:
            raise HTTPException(status_code=400, detail={"mensaje": "Errores de validación en el archivo", "errores": errores})

        if not cuentas_a_insertar:
            raise HTTPException(status_code=400, detail="No hay cuentas válidas para importar.")

        # 🔹 Inserción masiva con schema_name explícito
        insert_sql = text(f"""
            INSERT INTO {schema_name}.plan_cuentas 
            (id, codigo, nombre, tipo, naturaleza, acepta_tercero, nivel, cuenta_padre_id, empresa_id, activa, created_at)
            VALUES 
            (:id, :codigo, :nombre, :tipo, :naturaleza, :acepta_tercero, :nivel, :cuenta_padre_id, :empresa_id, true, NOW())
        """)
        
        for cuenta in cuentas_a_insertar:
            await db.execute(insert_sql, cuenta)
            
        await db.commit()
        
        return {"mensaje": f"Importación exitosa. {len(cuentas_a_insertar)} cuentas creadas."}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno al procesar el archivo: {str(e)}")
    
# ==========================================
# EXPORTAR PLAN DE CUENTAS A EXCEL
# ==========================================
async def exportar_plan_cuentas(empresa_id: UUID, db: AsyncSession, schema_name: str) -> io.BytesIO:
    """
    Consulta las cuentas activas de una empresa y genera un buffer de Excel en memoria.
    """
    # Consulta con subconsulta para obtener el código del padre (más útil para el usuario que el UUID)
    sql = text(f"""
        SELECT c.codigo, c.nombre, c.tipo, c.naturaleza, c.nivel, c.acepta_tercero,
               (SELECT p.codigo FROM {schema_name}.plan_cuentas p WHERE p.id = c.cuenta_padre_id) as cuenta_padre_codigo
        FROM {schema_name}.plan_cuentas c
        WHERE c.empresa_id = :empresa_id AND c.activa = true
        ORDER BY c.codigo
    """)
    
    result = await db.execute(sql, {"empresa_id": str(empresa_id)})
    rows = result.fetchall()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No hay cuentas activas para exportar en esta empresa.")
        
    # Crear DataFrame con las columnas exactas que espera el importador
    df = pd.DataFrame(rows, columns=[
        "codigo", "nombre", "tipo", "naturaleza", "nivel", "acepta_tercero", "cuenta_padre_codigo"
    ])
    
    # Generar Excel en memoria (sin escribir en disco)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="PlanCuentas")
    
    # Regresar el puntero al inicio del buffer para que pueda ser leído
    output.seek(0)
    return output