# app/services/sat_libros_service.py
from datetime import datetime
from decimal import Decimal

from app.models.global_models import TipoLibro
from app.models.tenant_models import FacturaElectronica, SatLibro, SatLibroLinea
from app.schemas.sat.sat_libros import SatLibroCreate
from fastapi import HTTPException, status
from sqlalchemy import delete, extract, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


async def procesar_y_generar_libro_sat(
    db: AsyncSession,
    payload: SatLibroCreate
) -> SatLibro:
    """
    Motor que extrae datos de FacturaElectronica y genera el libro SAT.
    """
    anio = payload.anio_periodo
    mes = payload.mes_periodo
    empresa_id = payload.empresa_id

    # 1. Validar y obtener el Tipo de Libro para determinar la operación
    tipo_libro_obj = await db.get(TipoLibro, payload.tipo_libro_id)
    if not tipo_libro_obj:
        raise HTTPException(status_code=404, detail="Tipo de libro no encontrado")
    
    # Asumimos que el código en la BD es 'compras' o 'ventas'
    tipo_operacion_db = "Compra" if tipo_libro_obj.codigo.lower() == "compras" else "Venta"

    # 2. Validar existencia y estado del libro en el tenant
    query_existente = select(SatLibro).where(
        SatLibro.empresa_id == empresa_id,
        SatLibro.tipo_libro_id == payload.tipo_libro_id,
        SatLibro.regimen_fiscal_id == payload.regimen_fiscal_id,
        SatLibro.anio_periodo == anio,
        SatLibro.mes_periodo == mes
    )
    result_existente = await db.execute(query_existente)
    libro_existente = result_existente.scalar_one_or_none()

    # Estados finales (asumimos IDs o códigos, aquí usamos lógica de negocio)
    # Si el libro ya está finalizado, no permitir modificación
    if libro_existente and libro_existente.finalizado_el is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El libro seleccionado ya se encuentra finalizado y no puede modificarse."
        )

    if libro_existente:
        # Limpieza de registros correlativos previos (Idempotencia)
        await db.execute(delete(SatLibroLinea).where(SatLibroLinea.libro_id == libro_existente.id))
        libro = libro_existente
    else:
        # ✅ CORREGIDO: Sin id=uuid4(). La BD genera el BIGINT.
        libro = SatLibro(
            empresa_id=empresa_id,
            tipo_libro_id=payload.tipo_libro_id,
            regimen_fiscal_id=payload.regimen_fiscal_id,
            estado_id=payload.estado_id,
            anio_periodo=anio,
            mes_periodo=mes,
        )
        db.add(libro)
        await db.flush() # Necesario para obtener libro.id antes de crear líneas

    # 3. Query optimizado a las facturas electrónicas activas del periodo
    query_facturas = select(FacturaElectronica).where(
        FacturaElectronica.empresa_id == empresa_id,
        func.lower(FacturaElectronica.tipo_operacion) == tipo_operacion_db.lower(),
        func.lower(FacturaElectronica.estado) == "activa",
        extract('year', FacturaElectronica.fecha_emision) == anio,
        extract('month', FacturaElectronica.fecha_emision) == mes
    ).order_by(FacturaElectronica.fecha_emision.asc())

    result_facturas = await db.execute(query_facturas)
    facturas = result_facturas.scalars().all()

    # Acumuladores contables
    total_lineas = 0
    acum_exento = Decimal("0.00")
    acum_base = Decimal("0.00")
    acum_iva = Decimal("0.00")
    acum_monto = Decimal("0.00")
    lineas_a_insertar = []

    # 4. Transformación y desglose de rubros SAT
    for idx, fac in enumerate(facturas, start=1):
        total_lineas += 1
        
        nit_linea = fac.emisor_nit if tipo_operacion_db == "Compra" else fac.receptor_nit
        razon_social_linea = fac.emisor_nombre if tipo_operacion_db == "Compra" else fac.receptor_nombre
        
        doc_identificador = f"{fac.serie} - {fac.numero}" if fac.serie else fac.numero
        
        # Determinación de Créditos y Débitos (Simplificado para ejemplo)
        credito_calc = fac.total_iva if tipo_operacion_db == "Compra" else Decimal("0.00")
        debito_calc = fac.total_iva if tipo_operacion_db == "Venta" else Decimal("0.00")
        
        acum_base += fac.total_gravado
        acum_iva += fac.total_iva
        acum_monto += fac.total
        acum_exento += fac.total_exento
        
        # Normalización a GTQ
        tc = float(fac.tipo_cambio or 1.0)
        monto_total_gtq = Decimal(str(float(fac.total) * tc))
        
        if fac.total_iva == 0.00:
            linea_data = {
                "monto_exento": Decimal(str(monto_total_gtq)),
                "base_imponible": Decimal("0.00"),
                "monto_iva": Decimal("0.00")
            }
        else:
            linea_data = {
                "monto_exento": Decimal("0.00"),
                "base_imponible": Decimal(str(float(fac.total_gravado) * tc)),
                "monto_iva": Decimal(str(float(fac.total_iva) * tc))
            }
            
        # ✅ CORREGIDO: Sin id=uuid4().
        nueva_linea = SatLibroLinea(
            libro_id=libro.id,
            factura_id=fac.id,
            numero_secuencia=idx,
            fecha_documento=fac.fecha_emision.date(),
            numero_documento=doc_identificador[:50],
            nit=nit_linea,
            razon_social=razon_social_linea,
            es_exento=fac.total_exento > 0,
            monto_total=monto_total_gtq,
            credito_fiscal=credito_calc,
            debito_fiscal=debito_calc,
            **linea_data
        )
        lineas_a_insertar.append(nueva_linea)

    if lineas_a_insertar:
        db.add_all(lineas_a_insertar)

    # 5. Asignación de sumatorias
    libro.total_lineas = total_lineas
    libro.total_exento = acum_exento
    libro.total_base_imponible = acum_base
    libro.total_iva = acum_iva
    libro.total_monto = acum_monto
    
    await db.commit()
    await db.refresh(libro)
    return libro


async def obtener_libro_detallado(
    db: AsyncSession,
    empresa_id: int,  # ✅ BIGINT
    tipo_libro_id: int,  # ✅ BIGINT
    anio: int,
    mes: int
) -> SatLibro | None:
    """Busca un libro por sus parámetros de periodo."""
    query = (
        select(SatLibro)
        .where(
            SatLibro.empresa_id == empresa_id,
            SatLibro.tipo_libro_id == tipo_libro_id,
            SatLibro.anio_periodo == anio,
            SatLibro.mes_periodo == mes
        )
        .options(selectinload(SatLibro.lineas))
    )
    result = await db.execute(query)
    libro = result.scalar_one_or_none()
    
    if libro:
        libro.lineas.sort(key=lambda x: x.numero_secuencia)
    return libro


async def finalizar_libro_sat(
    db: AsyncSession,
    libro_id: int,  # ✅ BIGINT
    usuario_id: int  # ✅ BIGINT
) -> SatLibro:
    """Cambia el estado de un libro a 'finalizado'."""
    query = select(SatLibro).where(SatLibro.id == libro_id).options(selectinload(SatLibro.lineas))
    result = await db.execute(query)
    libro = result.scalar_one_or_none()
    
    if not libro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El libro contable solicitado no existe.")
        
    if libro.finalizado_el is not None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El libro ya está finalizado.")

    libro.finalizado_por = usuario_id
    libro.finalizado_el = datetime.utcnow()
    
    await db.commit()
    await db.refresh(libro)
    return libro