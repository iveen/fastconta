from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from app.models.tenant_models import (
    InventarioBodega,
    InventarioImportacion,
    InventarioItem,
    InventarioProducto,
    InventarioToma,
)
from app.services.inventario.item_service import ItemService
from fastapi import UploadFile
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

COLUMNAS_ESPERADAS = {
    "codigo": ["codigo", "código", "cod", "sku"],
    "descripcion": ["descripcion", "descripción", "desc", "producto", "nombre"],
    "costo_unitario": ["costo", "costo_unitario", "costo unitario", "pu", "precio"],
    "unidad_medida": ["unidad", "unidad_medida", "um", "u/m"],
    "bodega": ["bodega", "bod", "almacen", "almacén"],
    "cantidad": ["cantidad", "cant", "qty", "existencia", "stock"],
}


class ImportService:
    """
    Servicio para importar inventarios desde archivos xlsx/csv.
    
    Responsabilidades:
    - Leer y validar archivos
    - Mapear columnas flexiblemente
    - Registrar auditoría de importación
    - Delegar inserción de items a ItemService (reutiliza lógica)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.item_service = ItemService(db)

    @staticmethod
    def _normalizar_columnas(df: pd.DataFrame) -> dict[str, str]:
        """Mapea nombres de columnas del archivo a nombres canónicos."""
        mapa: dict[str, str] = {}
        cols_lower = {c.lower().strip(): c for c in df.columns}
        
        for canonico, aliases in COLUMNAS_ESPERADAS.items():
            for alias in aliases:
                if alias in cols_lower:
                    mapa[canonico] = cols_lower[alias]
                    break
        
        requeridas = {"descripcion", "costo_unitario", "cantidad"}
        faltantes = requeridas - set(mapa.keys())
        
        if faltantes:
            raise ValueError(
                f"Columnas obligatorias faltantes: {sorted(faltantes)}. "
                f"Columnas detectadas: {list(df.columns)}"
            )
        
        return mapa

    @staticmethod
    async def leer_archivo(file: UploadFile) -> pd.DataFrame:
        """Lee un archivo xlsx/csv y retorna un DataFrame con strings."""
        filename = (file.filename or "").lower()
        await file.seek(0)
        
        if filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file.file, dtype=str)
        elif filename.endswith(".csv"):
            df = pd.read_csv(file.file, dtype=str, encoding="utf-8-sig")
        else:
            raise ValueError("Formato no soportado. Use .xlsx, .xls o .csv")
        
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how="all")
        return df

    @staticmethod
    def _validar_y_convertir(
        df: pd.DataFrame, mapa: dict[str, str]
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Valida filas y retorna (items_validos, errores)."""
        items_validos: list[dict[str, Any]] = []
        errores: list[dict[str, Any]] = []
        
        for idx, row in df.iterrows():
            fila_num = int(idx) + 2
            try:
                descripcion = str(
                    row.get(mapa.get("descripcion", ""), "")
                ).strip()
                
                if not descripcion:
                    raise ValueError("Descripción vacía")
                
                costo_raw = str(row[mapa["costo_unitario"]]).strip()
                costo_raw = costo_raw.replace(",", "").replace("Q", "").replace(" ", "")
                
                try:
                    costo = Decimal(costo_raw)
                    if costo < 0:
                        raise ValueError("Costo unitario negativo")
                except (InvalidOperation, ValueError):
                    raise ValueError(f"Costo unitario inválido: '{costo_raw}'")
                
                cant_raw = str(row[mapa["cantidad"]]).strip()
                cant_raw = cant_raw.replace(",", "").replace(" ", "")
                
                try:
                    cantidad = Decimal(cant_raw)
                    if cantidad < 0:
                        raise ValueError("Cantidad negativa")
                except (InvalidOperation, ValueError):
                    raise ValueError(f"Cantidad inválida: '{cant_raw}'")
                
                codigo = ImportService._limpiar_valor(
                    row.get(mapa.get("codigo", ""), None)
                )
                unidad = ImportService._limpiar_valor(
                    row.get(mapa.get("unidad_medida", ""), "UND"),
                    default="UND",
                )
                bodega = ImportService._limpiar_valor(
                    row.get(mapa.get("bodega", ""), None)
                )
                
                items_validos.append({
                    "codigo": codigo,
                    "descripcion": descripcion,
                    "costo_unitario": costo,
                    "unidad_medida": unidad,
                    "bodega_codigo": bodega,
                    "cantidad": cantidad,
                    "costo_total": (cantidad * costo).quantize(Decimal("0.01")),
                })
            except Exception as e:
                errores.append({"fila": fila_num, "mensaje": str(e)})
        
        return items_validos, errores

    @staticmethod
    def _limpiar_valor(valor: Any, default: str | None = None) -> str | None:
        """Convierte valores NaN/None a None o al default especificado."""
        if valor is None:
            return default
        
        s = str(valor).strip()
        if not s or s.lower() in ("nan", "none", ""):
            return default
        
        return s

    async def importar(
        self,
        toma: InventarioToma,
        file: UploadFile,
        usuario_id: int,
        modo: str = "REEMPLAZAR",
    ) -> InventarioImportacion:
        """
        Importa items desde archivo a una toma.
        
        Args:
            modo: 'REEMPLAZAR' borra items actuales; 'AGREGAR' conserva existentes.
        """
        if toma.estado != "BORRADOR":
            raise ValueError("Solo se puede importar en tomas en estado BORRADOR")
        
        if modo not in ("REEMPLAZAR", "AGREGAR"):
            raise ValueError("Modo debe ser REEMPLAZAR o AGREGAR")
        
        df = await self.leer_archivo(file)
        mapa = self._normalizar_columnas(df)
        items_validos, errores = self._validar_y_convertir(df, mapa)
        
        # Pre-cargar catálogos para evitar N+1
        stmt_bodegas = (
            select(InventarioBodega)
            .where(
                and_(
                    InventarioBodega.tenant_id == toma.tenant_id,
                    InventarioBodega.empresa_id == toma.empresa_id,
                    InventarioBodega.is_active.is_(True),
                )
            )
        )
        result_bodegas = await self.db.execute(stmt_bodegas)
        bodegas_map = {b.codigo: b for b in result_bodegas.scalars().all()}
        
        stmt_productos = (
            select(InventarioProducto)
            .where(
                and_(
                    InventarioProducto.tenant_id == toma.tenant_id,
                    InventarioProducto.empresa_id == toma.empresa_id,
                    InventarioProducto.codigo.isnot(None),
                )
            )
        )
        result_productos = await self.db.execute(stmt_productos)
        productos_map = {
            p.codigo: p 
            for p in result_productos.scalars().all() 
            if p.codigo
        }
        
        if modo == "REEMPLAZAR":
            await self.db.execute(
                InventarioItem.__table__.delete().where(
                    InventarioItem.toma_id == toma.id
                )
            )
        
        for item_data in items_validos:
            producto = (
                productos_map.get(item_data["codigo"]) 
                if item_data["codigo"] 
                else None
            )
            bodega = (
                bodegas_map.get(item_data["bodega_codigo"]) 
                if item_data["bodega_codigo"] 
                else None
            )
            
            item = InventarioItem(
                toma_id=toma.id,
                producto_id=producto.id if producto else None,
                bodega_id=bodega.id if bodega else None,
                created_by=usuario_id,
                updated_by=usuario_id,
                **item_data,
            )
            self.db.add(item)
        
        importacion = InventarioImportacion(
            toma_id=toma.id,
            archivo_original=file.filename or "archivo",
            formato="xlsx" if (file.filename or "").lower().endswith((".xlsx", ".xls")) else "csv",
            modo=modo,
            filas_procesadas=len(df),
            filas_validas=len(items_validos),
            filas_con_error=len(errores),
            errores=errores or None,
            created_by=usuario_id,
            updated_by=usuario_id,
        )
        self.db.add(importacion)
        
        # Recalcular totales vía ItemService
        await self.item_service.recalcular_totales(toma)
        
        await self.db.commit()
        await self.db.refresh(importacion)
        return importacion