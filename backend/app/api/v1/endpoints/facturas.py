from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.db.session import get_tenant_db
from app.models.tenant_models import FacturaElectronica, Empresa, FacturaDetalle, CuentaContable, DetallePartida, Partida
from app.schemas.factura import FacturaOut
from app.schemas.partida import PartidaOut, DetallePartidaOut
from app.services.fel_parser import parse_fel_xml
from uuid import UUID

router = APIRouter()

@router.post("/upload", response_model=List[FacturaOut], status_code=status.HTTP_201_CREATED)
async def upload_facturas(
    empresa_id: str = Query(..., description="ID de la empresa"),
    files: List[UploadFile] = File(..., description="Archivos XML de FEL"),
    db: AsyncSession = Depends(get_tenant_db)
):
    # Validar empresa
    result_emp = await db.execute(select(Empresa).where(Empresa.id == empresa_id))
    if not result_emp.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Empresa no encontrada")

    facturas = []
    for file in files:
        if not file.filename.endswith('.xml'):
            raise HTTPException(status_code=400, detail=f"El archivo {file.filename} no es un XML")
        content = await file.read()
        xml_str = content.decode('utf-8')
        datos = parse_fel_xml(xml_str)
        if not datos:
            raise HTTPException(status_code=400, detail=f"No se pudo parsear {file.filename}")

        # Extraer los items para guardarlos después
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
        )
        db.add(factura)
        await db.flush()

        # Guardar detalles
        for item in items_factura:
            detalle = FacturaDetalle(
                factura_id=factura.id,
                cantidad=item['cantidad'],
                descripcion=item['descripcion'],
                precio_unitario=item['precio_unitario'],
                total_linea=item['total_linea'],
                iva_linea=item.get('iva_linea', 0),
            )
            db.add(detalle)
        facturas.append(factura)

    await db.commit()
    # Recargar las facturas con sus detalles precargados
    ids = [f.id for f in facturas]
    stmt = (select(FacturaElectronica)
            .where(FacturaElectronica.id.in_(ids))
            .options(selectinload(FacturaElectronica.detalles)))
    result = await db.execute(stmt)
    facturas_cargadas = result.scalars().all()
    return [FacturaOut.model_validate(f) for f in facturas_cargadas]

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
    stmt = select(FacturaElectronica).where(FacturaElectronica.id == factura_id).options(selectinload(FacturaElectronica.detalles))
    result = await db.execute(stmt)
    factura = result.scalar_one_or_none()
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura