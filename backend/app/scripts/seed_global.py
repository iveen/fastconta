"""
Script de inicializacion de catalogos globales (Esquema public).
Arquitectura normalizada con tabla puente Regimen-Impuesto.
Idempotente: seguro de ejecutar multiples veces.
"""
import os
import sys
import uuid

# Ajustar ruta para importar modelos desde la raiz del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from passlib.context import CryptContext
from sqlalchemy.dialects.postgresql import insert

from app.db.session import SessionLocal
from app.models.global_models import (
    CatalogoImpuesto,
    CatalogoImpuestoEspecial,
    CatalogoMoneda,
    CategoriaActivoFijo,
    EstadoLibro,
    RegimenFiscal,
    RegimenImpuestoConfig,
    Role,
    TipoDomicilio,
    TipoDTE,
    TipoLibro,
    TipoPersona,
    User,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def upsert_record(model, unique_field: str, unique_value: str, **kwargs):
    """
    Funcion robusta de Upsert (Insertar o Actualizar) para PostgreSQL.
    Garantiza idempotencia y genera UUID si no se proporciona.
    """
    db = SessionLocal()
    try:
        if 'id' not in kwargs:
            kwargs['id'] = uuid.uuid4()
            
        stmt = insert(model).values(**kwargs)
        stmt = stmt.on_conflict_do_update(
            index_elements=[unique_field],
            set_={k: kwargs[k] for k in kwargs.keys() if k != unique_field and k != 'id'}
        )
        db.execute(stmt)
        db.commit()
        print(f"  [✓] {model.__name__:25} -> {unique_value}")
    except Exception as e:
        db.rollback()
        print(f"  [!] Error en {model.__name__} ({unique_value}): {e}")
    finally:
        db.close()

def get_record_id(model, unique_field: str, unique_value: str) -> str:
    """Obtiene el UUID de un registro ya existente."""
    db = SessionLocal()
    try:
        record = db.query(model).filter(getattr(model, unique_field) == unique_value).first()
        return str(record.id) if record else None
    finally:
        db.close()

def main():
    print("=" * 70)
    print(" INICIANDO CARGA DE CATALOGOS GLOBALES (BASE LEGAL GUATEMALA) ")
    print("=" * 70)

    # =========================================================================
    # 1. ROLES DE ACCESO (RBAC)
    # =========================================================================
    print("\n[1/8] Sembrando Roles de Acceso...")
    roles_data = [
        {"codigo": "superadmin", "nombre": "Super Administrador", "nivel_acceso": 100, "descripcion": "Acceso total al sistema"},
        {"codigo": "tenant_manager", "nombre": "Administrador de Firma", "nivel_acceso": 80, "descripcion": "Administra su firma y clientes"},
        {"codigo": "tenant_member", "nombre": "Contador de Firma", "nivel_acceso": 60, "descripcion": "Miembro de la firma con acceso asignado"},
        {"codigo": "tenant_client", "nombre": "Cliente", "nivel_acceso": 20, "descripcion": "Solo lectura de su propia empresa"}
    ]
    for r in roles_data:
        upsert_record(Role, "codigo", r["codigo"], **r)

    # =========================================================================
    # 2. CATALOGO BASE DE IMPUESTOS (Definicion general)
    # =========================================================================
    print("\n[2/8] Sembrando Catalogo Base de Impuestos...")
    impuestos_data = [
        {
            "codigo": "IVA_GENERAL", "nombre": "Impuesto al Valor Agregado",
            "descripcion_legal": "Art. 10 Ley 27-92. Tasa general del 12%.",
            "tasa_porcentaje": 12.00, "tasa_fija_monto": 0.00,
            "limite_inferior": 0.00, "limite_superior": None,
            "frecuencia_pago": "MENSUAL", "frecuencia_liquidacion": "MENSUAL"
        },
        {
            "codigo": "ISR", "nombre": "Impuesto sobre la Renta",
            "descripcion_legal": "Art. 36 Ley 26-92 / Art. 44-46 Ley 10-2012. Variable segun regimen.",
            "tasa_porcentaje": None, "tasa_fija_monto": 0.00, # Se define en la configuracion del regimen
            "limite_inferior": 0.00, "limite_superior": None,
            "frecuencia_pago": "VARIABLE", "frecuencia_liquidacion": "ANUAL"
        },
        {
            "codigo": "ISO", "nombre": "Impuesto Solidario",
            "descripcion_legal": "Art. 7 Ley 73-2008. 1% sobre Activos Netos o Ingresos Brutos.",
            "tasa_porcentaje": 1.00, "tasa_fija_monto": 0.00,
            "limite_inferior": 0.00, "limite_superior": None,
            "frecuencia_pago": "TRIMESTRAL", "frecuencia_liquidacion": "ANUAL"
        }
    ]
    for imp in impuestos_data:
        upsert_record(CatalogoImpuesto, "codigo", imp["codigo"], **imp)

    # =========================================================================
    # 3. REGIMENES FISCALES (Identidad del contribuyente)
    # =========================================================================
    print("\n[3/8] Sembrando Regimenes Fiscales...")
    regimenes_data = [
        {"codigo": "PC_MANUAL", "nombre": "Pequeno Contribuyente Manual", "descripcion": "Art. 45 Dec. 10-2012. 5% mensual. No genera credito fiscal."},
        {"codigo": "PC_FEL", "nombre": "Pequeno Contribuyente Electronico (FEL)", "descripcion": "Art. 45 Dec. 10-2012. 4% mensual. No genera credito fiscal."},
        {"codigo": "RG_UTILIDADES", "nombre": "Regimen General Sobre Utilidades", "descripcion": "Art. 44 Dec. 10-2012. 25% anual sobre utilidad neta."},
        {"codigo": "ROS", "nombre": "Regimen Opcional Simplificado", "descripcion": "Art. 46 Dec. 10-2012. 5% hasta Q30k, 7% + Q1500 sobre Q30k."},
        {"codigo": "RENTA_TRABAJO", "nombre": "Rentas del Trabajo (Asalariados)", "descripcion": "Art. 67 Dec. 26-92. Tabla progresiva mensual."}
    ]
    for reg in regimenes_data:
        upsert_record(RegimenFiscal, "codigo", reg["codigo"], **reg)

    # =========================================================================
    # 4. CONFIGURACION REGIMEN-IMPUESTO (LA TABLA PUENTE - CORAZON DEL SISTEMA)
    # =========================================================================
    print("\n[4/8] Sembrando Configuraciones Especificas Regimen-Impuesto...")
    
    # Helper para crear la configuracion puente
    def upsert_config(regimen_cod, imp_cod, config_data):
        regimen_id = get_record_id(RegimenFiscal, "codigo", regimen_cod)
        imp_id = get_record_id(CatalogoImpuesto, "codigo", imp_cod)
        if not regimen_id or not imp_id:
            print(f"  [!] Skip config: Falta regimen '{regimen_cod}' o impuesto '{imp_cod}'")
            return
        
        # El unique constraint es (regimen_id, impuesto_id)
        config_data["regimen_id"] = regimen_id
        config_data["impuesto_id"] = imp_id
        
        # Usamos un campo compuesto ficticio para el upsert, o manejamos el error
        # Para simplificar, verificamos si existe y actualizamos
        db = SessionLocal()
        try:
            existing = db.query(RegimenImpuestoConfig).filter_by(
                regimen_id=regimen_id, impuesto_id=imp_id
            ).first()
            if existing:
                for k, v in config_data.items():
                    setattr(existing, k, v)
                db.commit()
                print(f"  [✓] Config: {regimen_cod} + {imp_cod}")
            else:
                config_data["id"] = uuid.uuid4()
                new_config = RegimenImpuestoConfig(**config_data)
                db.add(new_config)
                db.commit()
                print(f"  [✓] Config: {regimen_cod} + {imp_cod}")
        except Exception as e:
            db.rollback()
            print(f"  [!] Error config {regimen_cod} + {imp_cod}: {e}")
        finally:
            db.close()

    # --- PC MANUAL ---
    upsert_config("PC_MANUAL", "IVA_GENERAL", {
        "tasa_porcentaje": 12.00, "es_acreditable": False, "es_retencion_definitiva": True, "requiere_autorizacion_sat": False
    })
    upsert_config("PC_MANUAL", "ISR", {
        "tasa_porcentaje": 5.00, "limite_superior": 300000.00, 
        "es_acreditable": False, "es_retencion_definitiva": True, "requiere_autorizacion_sat": False
    })

    # --- PC FEL ---
    upsert_config("PC_FEL", "IVA_GENERAL", {
        "tasa_porcentaje": 12.00, "es_acreditable": False, "es_retencion_definitiva": True, "requiere_autorizacion_sat": False
    })
    upsert_config("PC_FEL", "ISR", {
        "tasa_porcentaje": 4.00, "limite_superior": 300000.00, 
        "es_acreditable": False, "es_retencion_definitiva": True, "requiere_autorizacion_sat": False
    })

    # --- REGIMEN GENERAL ---
    upsert_config("RG_UTILIDADES", "IVA_GENERAL", {
        "tasa_porcentaje": 12.00, "es_acreditable": True, "es_retencion_definitiva": False, "requiere_autorizacion_sat": False
    })
    upsert_config("RG_UTILIDADES", "ISR", {
        "tasa_porcentaje": 25.00, "es_acreditable": False, "es_retencion_definitiva": False, "requiere_autorizacion_sat": False
    })
    upsert_config("RG_UTILIDADES", "ISO", {
        "tasa_porcentaje": 1.00, "es_acreditable": True, "es_retencion_definitiva": False, "requiere_autorizacion_sat": False
    })

    # --- ROS (Tramo 1: <= 30,000) ---
    upsert_config("ROS", "ISR", {
        "tasa_porcentaje": 5.00, "tasa_fija_monto": 0.00, "limite_inferior": 0.01, "limite_superior": 30000.00,
        "es_acreditable": False, "es_retencion_definitiva": True, "requiere_autorizacion_sat": False
    })
    # --- ROS (Tramo 2: > 30,000) ---
    # Nota: El backend debera sumar ambas reglas o aplicar la logica de tramos. 
    # Aqui guardamos la regla base del tramo superior para referencia.
    upsert_config("ROS", "ISR_TRAMO_2", { # Asumimos que creaste este codigo en CatalogoImpuesto o usamos el mismo ISR con logica en backend
        "tasa_porcentaje": 7.00, "tasa_fija_monto": 1500.00, "limite_inferior": 30000.01, "limite_superior": None,
        "es_acreditable": False, "es_retencion_definitiva": True, "requiere_autorizacion_sat": True
    })

    # =========================================================================
    # 5. CATALOGOS FISCALES Y DE PERSONAS
    # =========================================================================
    print("\n[5/8] Sembrando Tipos de Persona, Domicilio y Monedas...")
    
    for nombre in ["NATURAL", "JURIDICA"]:
        upsert_record(TipoPersona, "nombre", nombre)
        
    for nombre in ["FISCAL", "OPERATIVO", "SUCURSAL"]:
        upsert_record(TipoDomicilio, "nombre", nombre)

    monedas = [
        {"codigo_banguat": "01", "codigo_iso": "GTQ", "nombre": "Quetzal", "simbolo": "Q", "decimales": 2},
        {"codigo_banguat": "02", "codigo_iso": "USD", "nombre": "Dolar Estadounidense", "simbolo": "$", "decimales": 2}
    ]
    for m in monedas:
        upsert_record(CatalogoMoneda, "codigo_iso", m["codigo_iso"], **m)

    # =========================================================================
    # 6. CATEGORIAS DE ACTIVOS FIJOS (Base Legal: Decreto 10-2012, Art. 28)
    # =========================================================================
    print("\n[6/8] Sembrando Categorias de Activos Fijos con Descripcion Legal...")
    activos_data = [
        {
            "nombre": "Edificios", 
            "descripcion": "Edificios, construcciones e instalaciones adheridas a los inmuebles y sus mejoras.",
            "tasa_minima_anual": 0.00, 
            "tasa_maxima_anual": 5.00, 
            "vida_util_meses_default": 240
        },
        {
            "nombre": "Maquinaria y Equipo", 
            "descripcion": "Maquinaria, equipo, herramientas, aparatos, instrumentos y muebles de oficina.",
            "tasa_minima_anual": 0.00, 
            "tasa_maxima_anual": 10.00, 
            "vida_util_meses_default": 120
        },
        {
            "nombre": "Muebles y Enseres", 
            "descripcion": "Muebles y enseres de oficina y casa habitacion.",
            "tasa_minima_anual": 0.00, 
            "tasa_maxima_anual": 10.00, 
            "vida_util_meses_default": 120
        },
        {
            "nombre": "Vehiculos", 
            "descripcion": "Vehiculos automotores, embarcaciones y aeronaves.",
            "tasa_minima_anual": 0.00, 
            "tasa_maxima_anual": 20.00, 
            "vida_util_meses_default": 60
        },
        {
            "nombre": "Equipo de Computo", 
            "descripcion": "Equipo de computo, sistemas y programas de computacion (software).",
            "tasa_minima_anual": 0.00, 
            "tasa_maxima_anual": 33.33, 
            "vida_util_meses_default": 36
        }
    ]
    for act in activos_data:
        upsert_record(CategoriaActivoFijo, "nombre", act["nombre"], **act)

    # =========================================================================
    # 7. LIBROS CONTABLES
    # =========================================================================
    for nombre in ["Libro de Compras", "Libro de Ventas", "Libro Diario", "Libro Mayor"]:
        upsert_record(TipoLibro, "nombre", nombre)
        
    for nombre in ["BORRADOR", "FINALIZADO", "PRESENTADO_SAT"]:
        upsert_record(EstadoLibro, "nombre", nombre)

    # =========================================================================
    # 8. USUARIO SUPERADMIN INICIAL
    # =========================================================================
    print("\n[8/8] Sembrando Usuario Superadmin por defecto...")
    admin_role_id = get_record_id(Role, "codigo", "superadmin")
    if admin_role_id:
        upsert_record(User, "email", "admin@fastconta.com",
            full_name="Administrador del Sistema",
            hashed_password=pwd_context.hash("admin123"),
            role_id=admin_role_id,
            is_active=True,
            tenant_id=None
        )
    else:
        print("  [!] Advertencia: No se encontro el rol 'superadmin'.")
    
    # =========================================================================
    # 9. CATALOGO DE IMPUESTOS ESPECIALES (Leyes Especiales de Guatemala)
    # =========================================================================
    print("\n[9/10] Sembrando Catalogo de Impuestos Especiales...")
    
    # Estos impuestos aparecen en las columnas W-AG de las consultas FEL de la SAT
    # y deben RESTARSE del Gran Total antes de calcular el IVA (Art. 11 Ley 27-92)
    impuestos_especiales_data = [
        {
            "codigo": "PETROLEO",
            "nombre": "Petroleo",
            "descripcion": "Impuesto al Petroleo (Decreto 72-96). No es base para el calculo del IVA."
        },
        {
            "codigo": "TURISMO_HOSPEDAJE",
            "nombre": "Turismo Hospedaje",
            "descripcion": "Impuesto al Turismo por Hospedaje (Decreto 37-2014). No es base para el IVA."
        },
        {
            "codigo": "TURISMO_PASAJES",
            "nombre": "Turismo Pasajes",
            "descripcion": "Impuesto al Turismo por Pasajes Aereos. No es base para el IVA."
        },
        {
            "codigo": "TIMBRE_PRENSA",
            "nombre": "Timbre de Prensa",
            "descripcion": "Impuesto de Timbre de Prensa (Ley de Imprenta). No es base para el IVA."
        },
        {
            "codigo": "BEBIDAS",
            "nombre": "Bebidas Alcoholicas",
            "descripcion": "Impuesto Especifico a Bebidas Alcoholicas (Decreto 56-2013). No es base para el IVA."
        },
        {
            "codigo": "TABACO",
            "nombre": "Tabaco",
            "descripcion": "Impuesto Especifico a Productos de Tabaco (Decreto 56-2013). No es base para el IVA."
        },
        {
            "codigo": "CEMENTO",
            "nombre": "Cemento",
            "descripcion": "Impuesto Especifico al Cemento (Decreto 56-2013). No es base para el IVA."
        },
        {
            "codigo": "VEHICULOS_IPRIMA",
            "nombre": "Vehiculos (IPRIMA)",
            "descripcion": "Impuesto a la Primera Matrícula de Vehículos (Decreto 91-97). No es base para el IVA."
        }
    ]
    
    for imp_esp in impuestos_especiales_data:
        upsert_record(CatalogoImpuestoEspecial, "codigo", imp_esp["codigo"], **imp_esp)

    # =========================================================================
    # 10. TIPOS DE DTE (Documentos Tributarios Electronicos - SAT)
    # =========================================================================
    print("\n[10/10] Sembrando Tipos de DTE oficiales de la SAT...")
    
    dtes_data = [
        {
            "codigo": "FAC", 
            "nombre": "Factura", 
            "descripcion": "Documento que ampara la transferencia de bienes o prestacion de servicios.",
            "requiere_complemento": False, 
            "es_factura": True
        },
        {
            "codigo": "FPE", 
            "nombre": "Factura de Pequeno Contribuyente", 
            "descripcion": "Factura emitida por contribuyentes del regimen de pequeno contribuyente.",
            "requiere_complemento": False, 
            "es_factura": True
        },
        {
            "codigo": "FES", 
            "nombre": "Factura Especial", 
            "descripcion": "Factura emitida por pequeno contribuyente a sujetos obligados a llevar contabilidad.",
            "requiere_complemento": False, 
            "es_factura": True
        },
        {
            "codigo": "FEX", 
            "nombre": "Factura de Exportacion", 
            "descripcion": "Documento que ampara la exportacion de bienes o prestacion de servicios al exterior.",
            "requiere_complemento": False, 
            "es_factura": True
        },
        {
            "codigo": "NCR", 
            "nombre": "Nota de Credito", 
            "descripcion": "Documento que ampara devoluciones, descuentos o bonificaciones sobre una factura original.",
            "requiere_complemento": True,  # ⚠️ CRITICO: Obliga al sistema a pedir el numero de factura original
            "es_factura": False
        },
        {
            "codigo": "NDB", 
            "nombre": "Nota de Debito", 
            "descripcion": "Documento que ampara cargos adicionales o intereses sobre una factura original.",
            "requiere_complemento": True,  # ⚠️ CRITICO: Obliga al sistema a pedir el numero de factura original
            "es_factura": False
        },
        {
            "codigo": "CDE", 
            "nombre": "Certificado de Donacion", 
            "descripcion": "Documento que ampara donaciones deducibles de ISR.",
            "requiere_complemento": False, 
            "es_factura": False
        },
        {
            "codigo": "REE", 
            "nombre": "Factura de Regimen de Excepcion", 
            "descripcion": "Factura emitida por contribuyentes del regimen de excepcion (ISR).",
            "requiere_complemento": False, 
            "es_factura": True
        }
    ]
    
    for d in dtes_data:
        upsert_record(TipoDTE, "codigo", d["codigo"], **d)

    print("\n" + "=" * 70)
    print(" CARGA DE CATALOGOS GLOBALES COMPLETADA EXITOSAMENTE ")
    print("=" * 70)
    print("\n Credenciales de acceso por defecto:")
    print("  Email: admin@fastconta.com")
    print("  Password: admin123")
    print("  (Cambie esta contraseña inmediatamente en produccion)")

if __name__ == "__main__":
    main()