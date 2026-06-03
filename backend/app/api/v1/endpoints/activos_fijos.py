import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import (
    get_db,  # Ajusta esta importación a tu estructura real de dependencias
)
from app.schemas.activos_fijos import (
    ActivoFijoCreate,
    ActivoFijoResponse,
    ActivoFijoUpdate,
    CategoriaActivoFijoResponse,
    ProcesarDepreciacionMensualRequest,
    ProcesarDepreciacionMensualResponse,
    TablaDepreciacionProyectadaResponse,
)
from app.services import activos_fijos_service


# ==============================================================================
# DEPENDENCIAS DE SEGURIDAD (Placeholder)
# ==============================================================================
# En un entorno real, esta dependencia debe verificar que el usuario autenticado 
# tenga permiso para acceder a la empresa_id solicitada dentro de su tenant.
def verificar_acceso_empresa(empresa_id: uuid.UUID, db: Session = Depends(get_db)):
    # TODO: Implementar lógica real: 
    # 1. Obtener current_user de la request
    # 2. Verificar que current_user.tenant_id tenga acceso a esta empresa_id
    # 3. Si no, lanzar HTTPException(status_code=403, detail="Acceso no autorizado a esta empresa")
    return empresa_id

# ==============================================================================
# ROUTER
# ==============================================================================
router = APIRouter(prefix="/activos-fijos", tags=["Activos Fijos"])


# -----------------------------------------------------------------------------
# 1. CATÁLOGOS GLOBALES
# -----------------------------------------------------------------------------
@router.get("/categorias", response_model=list[CategoriaActivoFijoResponse])
def listar_categorias_activos(db: Session = Depends(get_db)):
    """
    Obtiene el catalogo global de categorias de activos fijos con sus limites de la SAT.
    No requiere empresa_id, ya que es un catalogo compartido (esquema public).
    """
    # Nota: Esta consulta asume que tienes un metodo en el servicio o la haces directa aqui.
    # Por simplicidad, la hacemos directa, filtrando solo las activas.
    from app.models.global_models import CategoriaActivoFijo
    
    categorias = db.query(CategoriaActivoFijo).filter(
        CategoriaActivoFijo.is_active == True
    ).all()
    
    return categorias


# -----------------------------------------------------------------------------
# 2. GESTIÓN DE ACTIVOS FIJOS (CRUD)
# -----------------------------------------------------------------------------
@router.get("/", response_model=list[ActivoFijoResponse])
def listar_activos(
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Lista los activos fijos registrados para una empresa especifica."""
    from app.models.tenant_models import ActivoFijo
    
    activos = db.query(ActivoFijo).filter(
        ActivoFijo.empresa_id == empresa_id
    ).offset(skip).limit(limit).all()
    
    return activos


@router.post("/", response_model=ActivoFijoResponse, status_code=status.HTTP_201_CREATED)
def crear_activo(
    data: ActivoFijoCreate,
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo activo fijo. 
    Valida automaticamente que la tasa de depreciacion no exceda el limite de la SAT.
    """
    # Forzamos que el empresa_id venga del contexto de seguridad, no del body
    data.empresa_id = empresa_id 
    return activos_fijos_service.crear_activo_fijo(db=db, empresa_id=empresa_id, data=data)


@router.get("/{activo_id}", response_model=ActivoFijoResponse)
def obtener_activo(
    activo_id: uuid.UUID,
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    db: Session = Depends(get_db)
):
    """Obtiene los detalles de un activo fijo especifico."""
    from app.models.tenant_models import ActivoFijo
    
    activo = db.query(ActivoFijo).filter(
        ActivoFijo.id == activo_id,
        ActivoFijo.empresa_id == empresa_id # Seguridad: asegura que pertenece a la empresa
    ).first()
    
    if not activo:
        raise HTTPException(status_code=404, detail="Activo fijo no encontrado o no pertenece a esta empresa")
    
    return activo


@router.put("/{activo_id}", response_model=ActivoFijoResponse)
def actualizar_activo(
    activo_id: uuid.UUID,
    data: ActivoFijoUpdate,
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    db: Session = Depends(get_db)
):
    """Actualiza la informacion de un activo fijo existente."""
    # Verificar propiedad antes de actualizar
    activo_existente = db.query(activos_fijos_service.ActivoFijo).filter(
        activos_fijos_service.ActivoFijo.id == activo_id,
        activos_fijos_service.ActivoFijo.empresa_id == empresa_id
    ).first()
    
    if not activo_existente:
        raise HTTPException(status_code=404, detail="Activo fijo no encontrado")

    return activos_fijos_service.actualizar_activo_fijo(db=db, activo_id=activo_id, data=data)


# -----------------------------------------------------------------------------
# 3. PROCESOS CONTABLES Y REPORTES
# -----------------------------------------------------------------------------
@router.post("/depreciacion-mensual", response_model=ProcesarDepreciacionMensualResponse)
def procesar_cierre_mensual(
    request: ProcesarDepreciacionMensualRequest,
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    db: Session = Depends(get_db)
):
    """
    Ejecuta el calculo de depreciacion de todos los activos de la empresa para un mes/anio dado.
    Genera una unica partida de diario en estado borrador para revision del contador.
    """
    # Validar que la empresa del request coincida con la autorizada
    if request.empresa_id != empresa_id:
        raise HTTPException(status_code=403, detail="No autorizado para procesar esta empresa")

    return activos_fijos_service.procesar_depreciacion_mensual(
        db=db,
        empresa_id=request.empresa_id,
        anio=request.anio_periodo,
        mes=request.mes_periodo
    )


@router.get("/{activo_id}/proyeccion", response_model=TablaDepreciacionProyectadaResponse)
def obtener_proyeccion_depreciacion(
    activo_id: uuid.UUID,
    empresa_id: uuid.UUID = Depends(verificar_acceso_empresa),
    db: Session = Depends(get_db)
):
    """
    Genera la tabla de depreciacion (historico + proyeccion futura) para un activo.
    Util para que el frontend muestre la tabla completa de vida util del activo.
    """
    # Verificar que el activo pertenezca a la empresa autorizada
    from app.models.tenant_models import ActivoFijo
    activo = db.query(ActivoFijo).filter(
        ActivoFijo.id == activo_id,
        ActivoFijo.empresa_id == empresa_id
    ).first()
    
    if not activo:
        raise HTTPException(status_code=404, detail="Activo no encontrado o acceso denegado")

    return activos_fijos_service.obtener_proyeccion_depreciacion(db=db, activo_id=activo_id)