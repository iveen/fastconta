# backend/app/api/v1/endpoints/facturas.py

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload
from typing import List
from app.db.session import get_tenant_db
from app.models.tenant_models import FacturaElectronica, Empresa, FacturaDetalle, CuentaContable, DetallePartida, Partida
from app.schemas.factura import FacturaOut
from app.schemas.partida import PartidaOut, DetallePartidaOut
from app.services.fel_parser import parse_fel_xml
from uuid import UUID, UUID as UUIDType
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=dict, status_code=status.HTTP_201_CREATED)
async def upload_facturas(
    empresa_id: str = Query(..., description="ID de la empresa"),
    files: List[UploadFile] = File(..., description="Archivos XML de FEL"),
    db: AsyncSession = Depends(get_tenant_db)
):
    user_info = db.info.get("current_user")
    schema_name = user_info.get("schema") if user_info else None
    if not schema_name:
        tenant_id = user_info.get("tenant_id") if user_info else None
        if not tenant_id:
            logger.error(f'Token Inválido para {schema_name}')
            raise HTTPException(status_code=400, detail="Token inválido")
        tenant_result = await db.execute(
            text("SELECT schema_name FROM public.tenants WHERE id = :tid"),
            {"tid": tenant_id}
        )
        tenant_row = tenant_result.fetchone()
        if not tenant_row:
            logger.error(f"Tenant {schema_name} no encontrado.")
            raise HTTPException(status_code=400, detail="Tenant no encontrado")
        schema_name = tenant_row[0]

    ## async with db.begin():
    try:
        await db.execute(text(f"SET search_path TO {schema_name}, public"))

        # Validar empresa
        emp_row = await db.execute(
            text(f"SELECT id, nit FROM {schema_name}.empresas WHERE id = :emp_id"),
            {"emp_id": empresa_id}
        )
        empresa = emp_row.fetchone()
        if not empresa:
            logger.error(f'Empresa {empresa_id} no encontrada.')
            raise HTTPException(status_code=400, detail="Empresa no encontrada")
        empresa_nit = empresa[1].strip() if empresa[1] else ""

        facturas = []
        log_rechazos = []

        for file in files:
            if not file.filename.endswith('.xml'):
                logger.warning(f'{file.filename} No es un archivo XML')
                log_rechazos.append(f"{file.filename}: No es un archivo XML")
                continue

            content = await file.read()
            logger.debug(f"📄 Archivo recibido: {file.filename}, size={len(content)}B, first_bytes={content[:100]}")
            xml_str = content.decode('utf-8')
            datos = parse_fel_xml(xml_str)
            if not datos:
                logger.warning(f'{file.filename}: No se pudo procesar')
                log_rechazos.append(f"{file.filename}: No se pudo parsear")
                continue

            # Verificar duplicado con SQL cualificado
            existente = await db.execute(
                text(f"SELECT id FROM {schema_name}.facturas_electronicas WHERE empresa_id = :emp_id AND serie = :serie AND numero_autorizacion = :num"),
                {"emp_id": empresa_id, "serie": datos.get('serie'), "num": datos.get('numero_autorizacion')}
            )
            if existente.fetchone():
                logger.warning(f"{file.filename}: Factura Duplicada")
                log_rechazos.append(f"{file.filename}: Factura duplicada")
                continue
            
            # Clasificar
            emisor_nit = datos.get('emisor_nit', '').replace('-', '')
            receptor_nit = datos.get('receptor_nit', '').replace('-', '')
            if emisor_nit == empresa_nit:
                tipo_op = 'Venta'
            elif receptor_nit == empresa_nit:
                tipo_op = 'Compra'
            else:
                logger.warning(f"{file.filename}: NITs no coinciden con la empresa")
                log_rechazos.append(f"{file.filename}: NITs no coinciden con la empresa")
                continue

            items_factura = datos.pop('items', [])

            factura = FacturaElectronica(
                empresa_id=empresa_id,
                xml_original=xml_str,
                numero_autorizacion=datos['numero_autorizacion'],
                autorizacion_uuid=datos.get('autorizacion_uuid'),
                serie=datos.get('serie'),
                numero=datos.get('numero'),
                tipo_documento=datos.get('tipo_documento'),
                moneda=datos.get('moneda'),
                fecha_emision=datos['fecha_emision'],
                emisor_nit=datos['emisor_nit'],
                emisor_nombre=datos['emisor_nombre'],
                receptor_nit=datos['receptor_nit'],
                receptor_nombre=datos['receptor_nombre'],
                total_gravado=datos['total_gravado'],
                total_iva=datos['total_iva'],
                total_exento=datos.get('total_exento', 0),
                total=datos['total'],
                es_exportacion=datos.get('es_exportacion', False),
                nombre_comercial=datos.get('emisor_nombre_comercial'),
                tipo_operacion=tipo_op,
                estado='Activa',
            )
            db.add(factura)
            await db.flush()

            for item in items_factura:
                db.add(FacturaDetalle(
                    factura_id=factura.id,
                    cantidad=item['cantidad'],
                    descripcion=item['descripcion'],
                    precio_unitario=item['precio_unitario'],
                    total_linea=item['total_linea'],
                    iva_linea=item.get('iva_linea', 0),
                ))

            facturas.append(factura)

        # Recargar dentro de la transacción para evitar problemas de conexión
        ids = [f.id for f in facturas]
        stmt = (select(FacturaElectronica)
                .where(FacturaElectronica.id.in_(ids))
                .options(selectinload(FacturaElectronica.detalles)))
        result = await db.execute(stmt)
        facturas_cargadas = result.scalars().all()
        await db.commit()

        return {
            "cargadas": len(facturas_cargadas),
            "facturas": [FacturaOut.model_validate(f) for f in facturas_cargadas],
            "rechazadas": log_rechazos
        }
    except Exception as e:
        # 🔹 Logging detallado SIEMPRE (para desarrollo)
        import traceback, os
        error_details = traceback.format_exc()
        logger.error(f"❌ Error procesando {file.filename}:\n{error_details}")
        
        # 🔹 Mostrar error detallado solo si estamos en desarrollo
        # Usamos variable de entorno estándar o fallback a True
        is_dev = os.getenv("ENVIRONMENT", "development") == "development"
        detail = f"{file.filename}: {str(e)}\n\n{error_details}" if is_dev else f"{file.filename}: No se pudo procesar la factura"
        
        raise HTTPException(status_code=400, detail=detail)

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