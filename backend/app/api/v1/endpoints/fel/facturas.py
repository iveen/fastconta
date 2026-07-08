# app/api/v1/endpoints/facturas.py
import logging
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.file_handlers import FileHandlerRegistry
from app.core.security import DataScope, get_data_scope
from app.db.session import get_public_db
from app.dependencies.empresa import get_active_empresa
from app.models.tenant_models import Empresa, FacturaElectronica
from app.schemas.contabilidad.partida import DetallePartidaOut, PartidaOut
from app.schemas.fel.factura import FacturaOut

# 🆕 Importar el nuevo servicio contable
from app.services.facturas.contabilidad_service import (
    clasificar_gasto_sat,
    generar_partida_desde_factura,
)
from app.services.facturas.tipo_cambio_service import obtener_tipo_cambio
from app.services.fel.context import FelIngestionContext

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================
# HELPER: Configurar search_path según rol
# ============================================================
async def _set_schema_for_query(
    db: AsyncSession,
    scope: DataScope,
    tenant_id: int | None = None
) -> str:
    """Configura el search_path correcto según el rol del usuario."""
    if scope.role_code == "superadmin":
        if not tenant_id:
            raise HTTPException(400, detail="Superadmin debe especificar un tenant_id")
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id}
        )
    else:
        res = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": scope.tenant_id}
        )
    row = res.first()
    if not row:
        raise HTTPException(404, detail="Tenant no encontrado")
    schema_name = row[0]
    if not schema_name.replace("_", "").isalnum():
        raise HTTPException(500, detail="Schema con formato inválido")
    await db.execute(text(f"SET LOCAL search_path TO {schema_name}, public"))
    return schema_name


# ============================================================
# 1. Upload de Facturas (coordinador, lógica delegada)
# ============================================================
@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_facturas(
    empresa_id: int | None = Query(None),
    tenant_id: int | None = Query(None),
    files: List[UploadFile] = File(...),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)
):
    # schema_name = await _set_schema_for_query(db, scope, tenant_id)
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    if not empresa_id_final:
        raise HTTPException(400, detail="Debe especificar una empresa")

    # Validar empresa y obtener NIT
    emp_nit_res = await db.execute(
        text("SELECT nit FROM empresas WHERE id = :eid"),
        {"eid": empresa_id_final}
    )
    empresa_nit = emp_nit_res.scalar_one().replace('-', '').strip()

    facturas_creadas = []
    rechazos = []

    for file in files:
        try:
            # 1. Delegar parseo al servicio FEL
            handler = FileHandlerRegistry.resolve(file.filename, file.content_type)
            content = await handler.read(file)
            result = await FelIngestionContext.ingest(content, db)

            if not result.success:
                rechazos.append(f"{file.filename}: {result.error}")
                continue

            datos = result.data

            # 2. Validar duplicados
            dup = await db.execute(
                text("""
                    SELECT id FROM facturas_electronicas 
                    WHERE empresa_id = :e AND numero_autorizacion = :n
                """),
                {"e": empresa_id_final, "n": datos.get('numero_autorizacion')}
            )
            if dup.first():
                rechazos.append(f"{file.filename}: Duplicada")
                continue

            # 3. Determinar tipo de operación
            em = datos.get('emisor_nit', '').replace('-', '')
            rec = datos.get('receptor_nit', '').replace('-', '')
            if em == empresa_nit:
                tipo_op = 'Venta'
            elif rec == empresa_nit:
                tipo_op = 'Compra'
            else:
                rechazos.append(f"{file.filename}: Empresa no participa")
                continue

            # 4. Clasificación de gasto (delegada al servicio)
            clasificacion_inicial = await clasificar_gasto_sat(datos)

            # 5. Obtener catálogos y tipo de cambio
            tc = Decimal("1.00000")
            if datos.get('moneda') != 'GTQ' and datos.get('fecha_emision'):
                tc = await obtener_tipo_cambio(datos['fecha_emision'].date(), datos['moneda'], db) or tc

            # 6. Crear factura (lógica de persistencia)
            factura = await _crear_factura_en_bd(
                db, datos, empresa_id_final, tipo_op,
                clasificacion_inicial, tc, file.filename, content
            )
            facturas_creadas.append(factura)

        except Exception as e:
            logger.error(f"Error en {file.filename}: {e}", exc_info=True)
            rechazos.append(f"{file.filename}: {str(e)}")

    await db.commit()
    return {
        "cargadas": len(facturas_creadas),
        "rechazadas": rechazos,
    }


# ============================================================
# 2. Generar Partida desde Factura (DELEGADO AL SERVICIO)
# ============================================================
@router.post(
    "/{factura_id}/generar-partida",
    response_model=PartidaOut,
    status_code=status.HTTP_201_CREATED
)
async def generar_partida_desde_factura_endpoint(
    factura_id: int,  # ✅ BIGINT
    empresa_id: int | None = Query(None),
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)
):
    schema_name = await _set_schema_for_query(db, scope, tenant_id)
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    if not empresa_id_final:
        raise HTTPException(400, detail="Debe especificar una empresa")

    # Obtener factura
    stmt = select(FacturaElectronica).where(
        FacturaElectronica.id == factura_id,
        FacturaElectronica.empresa_id == empresa_id_final
    )
    result = await db.execute(stmt)
    factura = result.scalar_one_or_none()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")

    try:
        # 🎯 DELEGAR toda la lógica contable al servicio
        partida = await generar_partida_desde_factura(
            db=db,
            factura=factura,
            empresa_id=empresa_id_final,
            schema_name=schema_name
        )
        await db.commit()
        await db.refresh(partida, ['detalles'])

        return PartidaOut(
            id=partida.id,
            numero_poliza=partida.numero_poliza,
            fecha=partida.fecha,
            descripcion=partida.descripcion,
            empresa_nombre="",
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
    except ValueError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error generando partida: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# ============================================================
# 3. Listar/Obtener/Anular (sin cambios significativos)
# ============================================================
@router.get("/", response_model=List[FacturaOut])
async def listar_facturas(
    empresa_id: int | None = Query(None),
    tenant_id: int | None = Query(None),
    scope: DataScope = Depends(get_data_scope),
    db: AsyncSession = Depends(get_public_db),
    empresa_from_header: Empresa | None = Depends(get_active_empresa)
):
    # schema_name = await _set_schema_for_query(db, scope, tenant_id)
    empresa_id_final = empresa_id or (empresa_from_header.id if empresa_from_header else None)
    stmt = (
        select(FacturaElectronica)
        .options(selectinload(FacturaElectronica.detalles))
        .order_by(FacturaElectronica.fecha_emision.desc())
    )
    if empresa_id_final:
        stmt = stmt.where(FacturaElectronica.empresa_id == empresa_id_final)
    result = await db.execute(stmt)
    return [FacturaOut.model_validate(f) for f in result.scalars().all()]


# ============================================================
# Helper privado: Crear factura en BD
# ============================================================
async def _crear_factura_en_bd(db, datos, empresa_id, tipo_op, clasificacion, tc, filename, content):
    """Helper para persistir la factura (puede moverse a otro servicio si crece)."""
    xml_original = content.parsed_data.get("xml_text", "") if content.parsed_data else None
    items = datos.pop('items', [])
    tc_float = float(tc)

    factura = FacturaElectronica(
        empresa_id=empresa_id,
        xml_original=xml_original,
        numero_autorizacion=datos['numero_autorizacion'],
        serie=datos.get('serie'),
        numero=datos.get('numero'),
        fecha_emision=datos['fecha_emision'],
        emisor_nit=datos['emisor_nit'],
        emisor_nombre=datos['emisor_nombre'],
        receptor_nit=datos['receptor_nit'],
        receptor_nombre=datos['receptor_nombre'],
        total_gravado=datos['total_gravado'],
        total_iva=datos['total_iva'],
        total_exento=datos.get('total_exento', 0),
        total=datos['total'],
        tipo_cambio=tc,
        total_gravado_gtq=float(datos['total_gravado']) * tc_float,
        total_iva_gtq=float(datos['total_iva']) * tc_float,
        total_exento_gtq=float(datos.get('total_exento', 0)) * tc_float,
        total_gtq=float(datos['total']) * tc_float,
        es_exportacion=datos.get('es_exportacion', False),
        tipo_operacion=tipo_op,
        estado='Activa',
        tipo_documento=datos.get('tipo_documento'),
        moneda=datos.get('moneda'),
        xml_filename=filename,
        clasificacion_gasto_sat=clasificacion,
    )
    db.add(factura)
    await db.flush()

    # Crear detalles
    from app.models.tenant_models import FacturaDetalle
    for it in items:
        db.add(FacturaDetalle(
            factura_id=factura.id,
            cantidad=it['cantidad'],
            descripcion=it['descripcion'],
            precio_unitario=it['precio_unitario'],
            total_linea=it['total_linea'],
            iva_linea=it.get('iva_linea', 0),
            precio_unitario_gtq=float(it['precio_unitario']) * tc_float,
            total_linea_gtq=float(it['total_linea']) * tc_float,
            iva_linea_gtq=float(it.get('iva_linea', 0)) * tc_float,
            bien_o_servicio=it.get('bien_o_servicio', 'B')
        ))

    return factura