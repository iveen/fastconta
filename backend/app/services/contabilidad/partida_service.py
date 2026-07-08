# app/services/partida_service.py
import logging
from datetime import date

from app.crud.secuencias import get_next_poliza
from app.models.tenant_models import CuentaContable, DetallePartida, Partida
from app.schemas.contabilidad.partida import DetallePartidaOut, PartidaOut
from app.services.contabilidad.periodos_service import validar_periodo_abierto_por_fecha
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)


class PartidaService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================
    # VALIDACIONES
    # ============================================================
    async def validar_cuentas(self, cuenta_ids: set[int]) -> dict[int, CuentaContable]:
        """Valida que todas las cuentas existan y estén activas"""
        result = await self.db.execute(
            select(CuentaContable)
            .options(selectinload(CuentaContable.empresa))
            .where(CuentaContable.id.in_(cuenta_ids))
        )
        cuentas = {c.id: c for c in result.scalars().all()}
        
        if len(cuentas) != len(cuenta_ids):
            raise ValueError("Una o más cuentas no existen")
        
        for cuenta in cuentas.values():
            if not cuenta.is_active:
                raise ValueError(f"La cuenta {cuenta.codigo} está inactiva")
        
        return cuentas

    async def validar_cuentas_unicas(self, cuenta_ids: list[int]) -> None:
        """Valida que no se repita la misma cuenta en una partida"""
        codigos = []
        for cuenta_id in cuenta_ids:
            # Obtener código de cada cuenta
            result = await self.db.execute(
                select(CuentaContable.codigo).where(CuentaContable.id == cuenta_id)
            )
            codigo = result.scalar_one_or_none()
            if codigo:
                codigos.append(codigo)
        
        if len(codigos) != len(set(codigos)):
            raise ValueError("No se permite usar la misma cuenta más de una vez en una partida")

    async def validar_empresa_unica(self, cuentas: dict[int, CuentaContable]) -> int:
        """Valida que todas las cuentas pertenezcan a la misma empresa"""
        empresa_ids = {c.empresa_id for c in cuentas.values()}
        if len(empresa_ids) > 1:
            raise ValueError("Todas las cuentas deben pertenecer a la misma empresa")
        return next(iter(empresa_ids))

    async def validar_poliza_unica(self, numero_poliza: str, empresa_id: int, partida_id_excluir: int | None = None) -> None:
        """Valida que el número de póliza no exista"""
        stmt = select(Partida).where(
            Partida.numero_poliza == numero_poliza,
            Partida.empresa_id == empresa_id
        )
        if partida_id_excluir:
            stmt = stmt.where(Partida.id != partida_id_excluir)
        
        result = await self.db.execute(stmt)
        if result.scalar_one_or_none():
            raise ValueError(f"El número de póliza '{numero_poliza}' ya existe para esta empresa")

    # ============================================================
    # GENERACIÓN DE PÓLIZA
    # ============================================================
    async def generar_numero_poliza(self, empresa_id: int, schema_name: str) -> str:
        """Genera el siguiente número de póliza"""
        return await get_next_poliza(self.db, empresa_id, schema_name)

    # ============================================================
    # CRUD
    # ============================================================
    async def crear_partida(
        self,
        fecha: date,
        descripcion: str,
        detalles: list[dict],
        numero_poliza: str | None = None,
        schema_name: str | None = None
    ) -> PartidaOut:
        """Crea una nueva partida contable"""
        # 1. Validar cuentas
        cuenta_ids = {d['cuenta_id'] for d in detalles}
        cuentas = await self.validar_cuentas(cuenta_ids)
        await self.validar_cuentas_unicas([d['cuenta_id'] for d in detalles])
        
        # 2. Validar empresa
        empresa_id = await self.validar_empresa_unica(cuentas)
        
        # 3. Validar período abierto
        await validar_periodo_abierto_por_fecha(self.db, empresa_id, fecha)
        
        # 4. Generar número de póliza
        if not numero_poliza:
            numero_poliza = await self.generar_numero_poliza(empresa_id, schema_name)
        else:
            await self.validar_poliza_unica(numero_poliza, empresa_id)
        
        # 5. Crear partida
        partida = Partida(
            fecha=fecha,
            descripcion=descripcion,
            numero_poliza=numero_poliza,
            empresa_id=empresa_id,
            tipo_origen='manual'
        )
        self.db.add(partida)
        await self.db.flush()
        
        # 6. Crear detalles
        for det in detalles:
            self.db.add(DetallePartida(
                partida_id=partida.id,
                cuenta_id=det['cuenta_id'],
                tipo_movimiento=det['tipo_movimiento'],
                monto=det['monto']
            ))
        
        await self.db.commit()
        await self.db.refresh(partida, ['detalles'])
        
        # 7. Construir respuesta
        empresa_nombre = cuentas[detalles[0]['cuenta_id']].empresa.nombre
        return self._construir_partida_out(partida, empresa_nombre, cuentas)

    async def modificar_partida(
        self,
        partida_id: int,
        fecha: date,
        descripcion: str,
        detalles: list[dict],
        numero_poliza: str | None = None
    ) -> PartidaOut:
        """Modifica una partida existente"""
        # 1. Obtener partida
        partida = await self.obtener_partida_por_id(partida_id)
        if not partida:
            raise ValueError("Partida no encontrada")
        
        if not partida.is_active:
            raise ValueError("No se puede modificar una partida eliminada")
        
        if partida.tipo_origen in ['cierre', 'reversion_cierre']:
            raise ValueError(f"No se puede modificar una póliza de {partida.tipo_origen.replace('_', ' ')}")
        
        # 2. Validar período abierto
        await validar_periodo_abierto_por_fecha(self.db, partida.empresa_id, fecha)
        
        # 3. Validar cuentas
        cuenta_ids = {d['cuenta_id'] for d in detalles}
        cuentas = await self.validar_cuentas(cuenta_ids)
        
        # 4. Eliminar detalles antiguos
        await self.db.execute(
            delete(DetallePartida).where(DetallePartida.partida_id == partida_id)
        )
        
        # 5. Actualizar cabecera
        partida.fecha = fecha
        partida.descripcion = descripcion
        
        if numero_poliza and numero_poliza != partida.numero_poliza:
            await self.validar_poliza_unica(numero_poliza, partida.empresa_id, partida_id)
            partida.numero_poliza = numero_poliza
        
        await self.db.flush()
        
        # 6. Insertar nuevos detalles
        for det in detalles:
            self.db.add(DetallePartida(
                partida_id=partida.id,
                cuenta_id=det['cuenta_id'],
                tipo_movimiento=det['tipo_movimiento'],
                monto=det['monto']
            ))
        
        await self.db.commit()
        await self.db.refresh(partida, ['detalles'])
        
        empresa_nombre = cuentas[detalles[0]['cuenta_id']].empresa.nombre
        return self._construir_partida_out(partida, empresa_nombre, cuentas)

    async def eliminar_partida(self, partida_id: int) -> None:
        """Elimina una partida (soft delete)"""
        partida = await self.obtener_partida_con_detalles(partida_id)
        if not partida:
            raise ValueError("Partida no encontrada")
        
        if not partida.is_active:
            return  # Idempotente
        
        if partida.tipo_origen in ['cierre', 'reversion_cierre']:
            raise ValueError(f"No se puede eliminar una póliza de {partida.tipo_origen.replace('_', ' ')}")
        
        # Validar período abierto
        await validar_periodo_abierto_por_fecha(self.db, partida.empresa_id, partida.fecha)
        
        # Soft delete
        partida.is_active = False
        for detalle in partida.detalles:
            detalle.is_active = False
        
        await self.db.commit()

    async def revertir_partida(
        self,
        partida_id: int,
        fecha_reversion: date | None = None,
        schema_name: str | None = None
    ) -> PartidaOut:
        """Revierte una partida creando una nueva con movimientos invertidos"""
        # 1. Obtener partida original
        stmt_original = text(f"""
            SELECT 
                p.id, p.numero_poliza, p.fecha, p.descripcion, p.empresa_id, 
                p.is_active, p.fue_revertida, p.tipo_origen,
                d.cuenta_id, d.tipo_movimiento, d.monto,
                c.codigo as cuenta_codigo, c.nombre as cuenta_nombre,
                e.nombre as empresa_nombre
            FROM {schema_name}.partidas p
            JOIN {schema_name}.detalle_partidas d ON p.id = d.partida_id
            JOIN {schema_name}.plan_cuentas c ON d.cuenta_id = c.id
            JOIN {schema_name}.empresas e ON c.empresa_id = e.id
            WHERE p.id = :partida_id
            ORDER BY d.id
        """)
        
        result = await self.db.execute(stmt_original, {"partida_id": partida_id})
        rows = result.all()
        
        if not rows:
            raise ValueError("Partida no encontrada")
        
        primera_fila = rows[0]
        
        # Validaciones
        if not primera_fila.is_active:
            raise ValueError("No se puede revertir una partida eliminada")
        
        if primera_fila.fue_revertida:
            raise ValueError("Esta partida ya fue revertida")
        
        if primera_fila.tipo_origen in ['cierre', 'reversion_cierre']:
            raise ValueError(f"No se puede revertir una póliza de {primera_fila.tipo_origen.replace('_', ' ')}")
        
        # 2. Determinar fecha de reversión
        fecha_rev = fecha_reversion or date.today()
        
        # 3. Validar período abierto
        await validar_periodo_abierto_por_fecha(self.db, primera_fila.empresa_id, fecha_rev)
        
        # 4. Generar nuevo número de póliza
        nuevo_numero_poliza = await self.generar_numero_poliza(primera_fila.empresa_id, schema_name)
        
        # 5. Crear partida de reversión
        desc_reversion = f"Reversión Póliza {primera_fila.numero_poliza} - {primera_fila.descripcion}"
        
        stmt_insert = text(f"""
            INSERT INTO {schema_name}.partidas 
            (fecha, descripcion, numero_poliza, empresa_id, is_active, fue_revertida, partida_reversion_id, tipo_origen, created_at)
            VALUES (:fecha, :descripcion, :numero_poliza, :empresa_id, true, false, NULL, 'reversion_cierre', NOW())
            RETURNING id, created_at
        """)
        
        result = await self.db.execute(stmt_insert, {
            "fecha": fecha_rev,
            "descripcion": desc_reversion,
            "numero_poliza": nuevo_numero_poliza,
            "empresa_id": primera_fila.empresa_id
        })
        
        partida_reversion_data = result.first()
        partida_reversion_id = partida_reversion_data.id
        created_at = partida_reversion_data.created_at
        
        # 6. Invertir detalles
        detalles_revertidos = []
        for row in rows:
            tipo_invertido = "haber" if row.tipo_movimiento == "debe" else "debe"
            
            stmt_detalle = text(f"""
                INSERT INTO {schema_name}.detalle_partidas 
                (partida_id, cuenta_id, tipo_movimiento, monto, is_active, created_at)
                VALUES (:partida_id, :cuenta_id, :tipo_movimiento, :monto, true, NOW())
            """)
            
            await self.db.execute(stmt_detalle, {
                "partida_id": partida_reversion_id,
                "cuenta_id": row.cuenta_id,
                "tipo_movimiento": tipo_invertido,
                "monto": float(row.monto)
            })
            
            detalles_revertidos.append({
                "cuenta_id": row.cuenta_id,
                "cuenta_codigo": row.cuenta_codigo,
                "cuenta_nombre": row.cuenta_nombre,
                "tipo_movimiento": tipo_invertido,
                "monto": float(row.monto)
            })
        
        # 7. Marcar partida original como revertida
        stmt_update = text(f"""
            UPDATE {schema_name}.partidas 
            SET fue_revertida = true, partida_reversion_id = :partida_reversion_id
            WHERE id = :partida_id
        """)
        
        await self.db.execute(stmt_update, {
            "partida_reversion_id": partida_reversion_id,
            "partida_id": partida_id
        })
        
        await self.db.commit()
        
        # 8. Construir respuesta
        return PartidaOut(
            id=partida_reversion_id,
            numero_poliza=nuevo_numero_poliza,
            fecha=fecha_rev,
            descripcion=desc_reversion,
            empresa_nombre=primera_fila.empresa_nombre or "",
            created_at=created_at,
            is_active=True,
            fue_revertida=False,
            tipo_origen='reversion_cierre',
            detalles=[
                DetallePartidaOut(
                    id=det["cuenta_id"],
                    cuenta_id=det["cuenta_id"],
                    cuenta_codigo=det["cuenta_codigo"],
                    cuenta_nombre=det["cuenta_nombre"],
                    tipo_movimiento=det["tipo_movimiento"],
                    monto=det["monto"]
                ) for det in detalles_revertidos
            ]
        )

    # ============================================================
    # QUERIES
    # ============================================================
    async def obtener_partida_por_id(self, partida_id: int) -> Partida | None:
        """Obtiene una partida por ID"""
        stmt = select(Partida).where(Partida.id == partida_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def obtener_partida_con_detalles(self, partida_id: int) -> Partida | None:
        """Obtiene una partida con sus detalles"""
        stmt = (
            select(Partida)
            .options(selectinload(Partida.detalles))
            .where(Partida.id == partida_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def listar_partidas(self, empresa_id: int | None = None) -> list[Partida]:
        """Lista partidas con filtros opcionales"""
        stmt = (
            select(Partida)
            .options(
                selectinload(Partida.detalles)
                .selectinload(DetallePartida.cuenta)
                .selectinload(CuentaContable.empresa),
                selectinload(Partida.empresa)
            )
            .order_by(Partida.fecha.desc())
        )
        
        if empresa_id:
            stmt = stmt.where(Partida.empresa_id == empresa_id)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def obtener_libro_diario(
        self,
        empresa_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> list[dict]:
        """Obtiene el libro diario para un período"""
        stmt = (
            select(Partida, DetallePartida, CuentaContable)
            .join(DetallePartida, Partida.id == DetallePartida.partida_id)
            .join(CuentaContable, DetallePartida.cuenta_id == CuentaContable.id)
            .where(
                CuentaContable.empresa_id == empresa_id,
                Partida.fecha >= fecha_inicio,
                Partida.fecha <= fecha_fin
            )
            .order_by(Partida.fecha, Partida.numero_poliza, CuentaContable.codigo)
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        lineas = []
        for partida, detalle, cuenta in rows:
            lineas.append({
                "partida_id": partida.id,
                "numero_poliza": partida.numero_poliza,
                "fecha": partida.fecha,
                "descripcion": partida.descripcion,
                "cuenta_id": cuenta.id,
                "cuenta_codigo": cuenta.codigo,
                "cuenta_nombre": cuenta.nombre,
                "tipo_movimiento": detalle.tipo_movimiento,
                "monto": detalle.monto
            })
        
        return lineas

    # ============================================================
    # HELPERS
    # ============================================================
    def _construir_partida_out(
        self,
        partida: Partida,
        empresa_nombre: str,
        cuentas: dict[int, CuentaContable]
    ) -> PartidaOut:
        """Construye el objeto de respuesta"""
        return PartidaOut(
            id=partida.id,
            numero_poliza=partida.numero_poliza,
            fecha=partida.fecha,
            descripcion=partida.descripcion,
            empresa_nombre=empresa_nombre,
            created_at=partida.created_at,
            is_active=partida.is_active,
            fue_revertida=partida.fue_revertida,
            tipo_origen=partida.tipo_origen,
            detalles=[
                DetallePartidaOut(
                    id=det.id,
                    cuenta_id=det.cuenta_id,
                    cuenta_codigo=cuentas[det.cuenta_id].codigo,
                    cuenta_nombre=cuentas[det.cuenta_id].nombre,
                    tipo_movimiento=det.tipo_movimiento,
                    monto=det.monto
                ) for det in partida.detalles
            ]
        )