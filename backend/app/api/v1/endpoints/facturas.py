# backend/app/api/v1/endpoints/facturas.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from typing import List
from app.db.session import get_tenant_db
from app.models.tenant_models import FacturaElectronica, FacturaDetalle, CuentaContable, DetallePartida, Partida
from app.models.global_models import TipoDTE, CatalogoMoneda
from app.schemas.factura import FacturaOut
from app.schemas.partida import PartidaOut, DetallePartidaOut
from app.services.fel_parser import parse_fel_xml
from app.services.banguat_ws import obtener_tipo_cambio
from uuid import UUID, UUID as UUIDType
from openpyxl import load_workbook
import xlrd
from io import BytesIO
from decimal import Decimal
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

#------------------------------------
@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_facturas(
    empresa_id: str = Query(...),
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_tenant_db)
):
    user_info = db.info.get("current_user")
    schema_name = user_info.get("schema") or user_info.get("tenant_schema")
    if not schema_name and user_info.get("tenant_id"):
        res = await db.execute(text("SELECT schema_name FROM public.tenants WHERE id = :tid"), {"tid": user_info["tenant_id"]})
        row = res.fetchone()
        schema_name = row[0] if row else None

    if not schema_name:
        raise HTTPException(400, "Schema no determinado")

    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    
    # Validar empresa
    emp = await db.execute(text(f"SELECT id, nit FROM empresas WHERE id = :eid"), {"eid": empresa_id})
    emp_row = emp.fetchone()
    if not emp_row: raise HTTPException(400, "Empresa no encontrada")
    empresa_nit = emp_row[1].replace('-', '').strip()

    facturas_creadas = []
    rechazos = []

    for file in files:
        if not file.filename.endswith('.xml'):
            rechazos.append(f"{file.filename}: No es XML")
            continue
        
        try:
            xml_str = (await file.read()).decode('utf-8')
            datos = await parse_fel_xml(xml_str, db)
            if not datos: 
                rechazos.append(f"{file.filename}: Parse fallido")
                continue

            # Duplicado
            dup = await db.execute(text("SELECT id FROM facturas_electronicas WHERE empresa_id = :e AND serie = :s AND numero_autorizacion = :n"),
                                   {"e": empresa_id, "s": datos.get('serie'), "n": datos.get('numero_autorizacion')})
            if dup.fetchone():
                rechazos.append(f"{file.filename}: Duplicada")
                continue

            # Clasificar
            em = datos.get('emisor_nit','').replace('-','')
            rec = datos.get('receptor_nit','').replace('-','')
            tipo_op = 'Venta' if em == empresa_nit else ('Compra' if rec == empresa_nit else 'Terceros')

            # Resolver catálogos
            res_tipo = await db.execute(select(TipoDTE.id).where(TipoDTE.codigo == datos.get('tipo_documento','FACT')))
            tipo_id = res_tipo.scalar_one_or_none()
            res_mon = await db.execute(select(CatalogoMoneda.id).where(CatalogoMoneda.codigo_iso == datos.get('moneda','GTQ')))
            mon_id = res_mon.scalar_one_or_none()

            # Tipo de cambio
            tc = Decimal("1.00000")
            if datos.get('moneda') != 'GTQ' and datos.get('fecha_emision'):
                tc = await obtener_tipo_cambio(datos['fecha_emision'].date(), datos['moneda'], db) or tc

            items = datos.pop('items', [])
            factura = FacturaElectronica(
                empresa_id=empresa_id, xml_original=xml_str,
                numero_autorizacion=datos['numero_autorizacion'], serie=datos.get('serie'), numero=datos.get('numero'),
                fecha_emision=datos['fecha_emision'], emisor_nit=datos['emisor_nit'], emisor_nombre=datos['emisor_nombre'],
                receptor_nit=datos['receptor_nit'], receptor_nombre=datos['receptor_nombre'],
                total_gravado=datos['total_gravado'], total_iva=datos['total_iva'], total_exento=datos.get('total_exento',0), total=datos['total'],
                tipo_documento_id=tipo_id, moneda_id=mon_id, tipo_cambio=tc,
                es_exportacion=datos.get('es_exportacion', False), tipo_operacion=tipo_op, estado='Activa',
                tipo_documento=datos.get('tipo_documento'), moneda=datos.get('moneda'),
                xml_filename=file.filename,
            )
            db.add(factura)
            await db.flush()

            for it in items:
                db.add(FacturaDetalle(factura_id=factura.id, **it))
            facturas_creadas.append(factura)
        except Exception as e:
            logger.error(f"Error en {file.filename}: {e}")
            rechazos.append(f"{file.filename}: {str(e)}")

    await db.commit()
    return {"cargadas": len(facturas_creadas), "rechazadas": rechazos}

#------------------------------------
@router.post("/validar-hoja-electronica", status_code=status.HTTP_200_OK)
async def validar_hoja_electronica(
    file: UploadFile = File(...),
    empresa_id: str = Query(...),  # ✅ NUEVO: Declarar query param
    db: AsyncSession = Depends(get_tenant_db)
):
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(400, "Solo se permiten archivos Excel (.xlsx/.xls)")

    try:
        content = await file.read()

        SHEET_NAME = "InformacionDTE-FEL"  # ✅ Nombre explícito del worksheet
        rows = []

        # 🔹 Lectura según formato del archivo
        if file.filename.endswith('.xls'):
            # Usar xlrd==1.2.0 para archivos .xls antiguos (binarios)
            book = xlrd.open_workbook(file_contents=content)
            
            # Verificar que la hoja existe
            if SHEET_NAME not in book.sheet_names():
                raise HTTPException(400, f"La hoja '{SHEET_NAME}' no existe en el archivo")
            
            ws = book.sheet_by_name(SHEET_NAME)
            
            # Leer filas saltando encabezado (fila 0)
            for row_idx in range(1, ws.nrows):
                row = [ws.cell_value(row_idx, col) for col in range(ws.ncols)]
                rows.append(row)
        else:
            # Usar openpyxl para archivos .xlsx modernos (XML)
            wb = load_workbook(filename=BytesIO(content), data_only=True, read_only=True)
            
            # Verificar que la hoja existe
            if SHEET_NAME not in wb.sheetnames:
                wb.close()
                raise HTTPException(400, f"La hoja '{SHEET_NAME}' no existe en el archivo")
            
            ws = wb[SHEET_NAME]
            rows = list(ws.iter_rows(min_row=2, values_only=True))  # Saltar encabezado
            wb.close()

        # Mapeo de columnas (índice 0-based según tu Excel)
        COL_AUTH = 1
        COL_ANULADO = 20
        COL_FECHA_ANULADO = 21
        COLS_IMPUESTOS = {
            22: 'petroleo', 23: 'turismo_hospedaje', 24: 'turismo_pasajes',
            25: 'timbre_prensa', 26: 'bomberos', 27: 'tasa_municipal',
            28: 'bebidas_alcoholicas', 29: 'tabaco', 30: 'cemento',
            31: 'bebidas_no_alcoholicas', 32: 'tarifa_portuaria'
        }

        pendientes = []
        actualizadas = 0
        impuestos_insertados = 0

        for row in rows:
            if not row or not row[COL_AUTH]: 
                continue
            
            # 🔹 1. Normalizar el valor del Excel: quitar .xml, espacios y unificar caso
            auth_raw = str(row[COL_AUTH]).strip()
            if not auth_raw:
                continue
            auth_clean = auth_raw.replace('.xml', '').replace('.XML', '').strip().upper()

            # 🔹 2. Buscar factura en BD usando xml_filename (normalizado)
            res = await db.execute(
                text("""
                    SELECT id, estado 
                    FROM facturas_electronicas 
                    WHERE REPLACE(UPPER(xml_filename), '.XML', '') = :auth
                """),
                {"auth": auth_clean}
            )
            factura_row = res.fetchone()

            if not factura_row:
                pendientes.append(auth_clean)
                continue
            else:
                await db.execute(
                    text("""
                        UPDATE facturas_electronicas 
                        SET validado = TRUE, fecha_validacion = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """),
                    {"id": factura_row.id}
    )

            # 1. Actualizar estado de anulación si aplica
            marca_anulado = str(row[COL_ANULADO]).strip() if row[COL_ANULADO] else "No"
            
            # ✅ CORREGIDO: Comparar con estado, no con columna booleana
            if marca_anulado.lower() == "si" and factura_row.estado != "Anulada":
                fecha_anul = row[COL_FECHA_ANULADO]
                if isinstance(fecha_anul, str):
                    fecha_anul = datetime.fromisoformat(fecha_anul.replace("Z", "+00:00"))
                
                await db.execute(
                    text("""
                        UPDATE facturas_electronicas 
                        SET estado = 'Anulada', fecha_anulacion = :fecha
                        WHERE id = :id
                    """),
                    {"fecha": fecha_anul, "id": factura_row.id}
                )
                actualizadas += 1

            # 2. Insertar impuestos especiales (solo si monto > 0)
            for col_idx, tipo in COLS_IMPUESTOS.items():
                monto_val = row[col_idx]
                if monto_val and float(monto_val) > 0:
                    monto_dec = Decimal(str(monto_val))
                    existente = await db.execute(
                        text("SELECT id FROM facturas_impuestos_especiales WHERE factura_id = :fid AND tipo_codigo = :tipo"),
                        {"fid": factura_row.id, "tipo": tipo}
                    )
                    if not existente.fetchone():
                        await db.execute(
                            text("""
                                INSERT INTO facturas_impuestos_especiales (id, factura_id, tipo_codigo, monto)
                                VALUES (gen_random_uuid(), :fid, :tipo, :monto)
                            """),
                            {"fid": factura_row.id, "tipo": tipo, "monto": monto_dec}
                        )
                        impuestos_insertados += 1

        await db.commit()

        if pendientes:
            return {
                "success": False,
                "mensaje": "Validación rechazada. Faltan cargar los siguientes XML antes de validar:",
                "pendientes": pendientes,
                "procesadas": actualizadas,
                "impuestos_registrados": impuestos_insertados
            }

        return {
            "success": True,
            "mensaje": "Validación exitosa. Estados e impuestos sincronizados.",
            "anulaciones_actualizadas": actualizadas,
            "impuestos_registrados": impuestos_insertados
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Error procesando hoja electrónica: {str(e)}")
#--------------------------------------------------------


@router.get("/", response_model=List[FacturaOut])
async def listar_facturas(
    empresa_id: str = Query(None, description="Filtrar por empresa"),
    db: AsyncSession = Depends(get_tenant_db)
):
    stmt = (select(FacturaElectronica)
        .options(selectinload(FacturaElectronica.detalles))  # ← Precargar detalles
        .order_by(FacturaElectronica.fecha_emision.desc()))
    if empresa_id:
        stmt = stmt.where(FacturaElectronica.empresa_id == empresa_id)
    result = await db.execute(stmt)
    return [FacturaOut.model_validate(f) for f in result.scalars().all()]

@router.post("/{factura_id}/generar-partida", response_model=PartidaOut, status_code=status.HTTP_201_CREATED)
async def generar_partida_desde_factura(
    factura_id: str,
    empresa_id: UUID = Query(..., description="ID de la empresa"),
    db: AsyncSession = Depends(get_tenant_db)
):
    # 1. Validar que la factura exista y pertenezca a la empresa
    stmt = select(FacturaElectronica).where(
        FacturaElectronica.id == factura_id,
        FacturaElectronica.empresa_id == empresa_id
    )
    result = await db.execute(stmt)
    factura = result.scalar_one_or_none()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    # 2. Determinar el tipo de partida (compra o venta) según el emisor/receptor
    # Si el emisor es la empresa del tenant -> es una venta (ingreso)
    # Si el receptor es la empresa del tenant -> es una compra (gasto)
    # Esta lógica puede personalizarse según la configuración de la empresa
    # Por simplicidad, asumiremos que la factura cargada es una compra (gasto)
    # Para identificar automáticamente, se podría comparar el NIT de la empresa con emisor/receptor

    # 3. Obtener las cuentas contables necesarias
    # Buscar cuenta de IVA (código 1.1.4 por defecto)
    cuenta_iva = await db.execute(
        select(CuentaContable).where(
            CuentaContable.empresa_id == empresa_id,
            CuentaContable.codigo == "1.1.4"  # IVA por Cobrar
        )
    )
    cuenta_iva = cuenta_iva.scalar_one_or_none()

    # Buscar cuenta de gasto genérica (o usar la cuenta 5.1 Costo de Ventas)
    cuenta_gasto = await db.execute(
        select(CuentaContable).where(
            CuentaContable.empresa_id == empresa_id,
            CuentaContable.codigo == "5.1"  # Costo de Ventas
        )
    )
    cuenta_gasto = cuenta_gasto.scalar_one_or_none()

    # Buscar cuenta de proveedores (2.1.1)
    cuenta_proveedor = await db.execute(
        select(CuentaContable).where(
            CuentaContable.empresa_id == empresa_id,
            CuentaContable.codigo == "2.1.1"  # Proveedores
        )
    )
    cuenta_proveedor = cuenta_proveedor.scalar_one_or_none()

    if not all([cuenta_iva, cuenta_gasto, cuenta_proveedor]):
        raise HTTPException(
            status_code=400,
            detail="Faltan cuentas contables necesarias (1.1.4 IVA, 5.1 Costo de Ventas, 2.1.1 Proveedores)"
        )

    # 4. Construir detalles de la partida
    detalles_partida = []

    # Línea de gasto (total gravado)
    if factura.total_gravado > 0:
        detalles_partida.append({
            "cuenta_id": cuenta_gasto.id,
            "tipo_movimiento": "debe",
            "monto": factura.total_gravado
        })

    # Línea de IVA (si aplica)
    if factura.total_iva > 0:
        detalles_partida.append({
            "cuenta_id": cuenta_iva.id,
            "tipo_movimiento": "debe",
            "monto": factura.total_iva
        })

    # Línea de proveedor (total factura)
    detalles_partida.append({
        "cuenta_id": cuenta_proveedor.id,
        "tipo_movimiento": "haber",
        "monto": factura.total
    })

    # 5. Validar partida doble
    total_debe = sum(d["monto"] for d in detalles_partida if d["tipo_movimiento"] == "debe")
    total_haber = sum(d["monto"] for d in detalles_partida if d["tipo_movimiento"] == "haber")
    if total_debe != total_haber:
        raise HTTPException(status_code=400, detail="La partida no cuadra (debe ≠ haber)")

    # 6. Crear la partida
    partida = Partida(
        fecha=factura.fecha_emision.date(),
        descripcion=f"Factura {factura.serie} {factura.numero} - {factura.emisor_nombre}",
        numero_poliza=f"FEL-{factura.numero_autorizacion}",
    )
    db.add(partida)
    await db.flush()

    for det in detalles_partida:
        db.add(DetallePartida(
            partida_id=partida.id,
            cuenta_id=det["cuenta_id"],
            tipo_movimiento=det["tipo_movimiento"],
            monto=det["monto"]
        ))

    await db.commit()

    # 7. Retornar la partida generada
    return PartidaOut(
        id=partida.id,
        numero=partida.numero,
        numero_poliza=partida.numero_poliza,
        fecha=partida.fecha,
        descripcion=partida.descripcion,
        empresa_nombre="",  # Se podría llenar si se obtiene la empresa
        created_at=partida.created_at,
        detalles=[
            DetallePartidaOut(
                id=d.id,
                cuenta_id=d.cuenta_id,
                cuenta_codigo=d.cuenta.codigo if d.cuenta else "",
                cuenta_nombre=d.cuenta.nombre if d.cuenta else "",
                tipo_movimiento=d.tipo_movimiento,
                monto=d.monto
            ) for d in partida.detalles
        ]
    )

@router.get("/{factura_id}", response_model=FacturaOut)
async def get_factura(
    factura_id: str,
    db: AsyncSession = Depends(get_tenant_db)
):
    try:
        uuid_obj = UUID(factura_id)
    except ValueError:
        logger.warning(f"UUID inválido recibido: {factura_id}")
        raise HTTPException(
            status_code=400,
            detail=f"ID de factura inválido.  Formato esperado: UUID (ej: 550e8400-e29b-41d4-a716-446655440000)"
        )
    stmt = select(FacturaElectronica).where(
        FacturaElectronica.id == uuid_obj).options(selectinload(FacturaElectronica.detalles)
    )
    result = await db.execute(stmt)
    factura = result.scalar_one_or_none()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura

@router.patch("/{factura_id}/anular", response_model=FacturaOut)
async def anular_factura(
    factura_id: str,
    db: AsyncSession = Depends(get_tenant_db)
):
    stmt = (select(FacturaElectronica)
            .where(FacturaElectronica.id == factura_id)
            .options(selectinload(FacturaElectronica.detalles)))
    result = await db.execute(stmt)
    factura = result.scalar_one_or_none()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    if factura.estado == "Anulada":
        raise HTTPException(status_code=400, detail="La factura ya está anulada")

    factura.estado = "Anulada"
    await db.commit()
    await db.refresh(factura)
    return FacturaOut.model_validate(factura)