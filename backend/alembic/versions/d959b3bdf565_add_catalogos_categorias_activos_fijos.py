"""add_modelos_activos_fijos (Raw SQL)

Revision ID: 773aab3dc84c
Revises: fa5c063af104
Create Date: 2026-06-03 12:36:19.239825
"""
import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '773aab3dc84c'
down_revision: Union[str, None] = 'fa5c063af104'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Proteger el esquema 'system' (superadmin) de recibir tablas de datos de tenant
    schema_actual = os.environ.get("TENANT_SCHEMA", "public")
    if schema_actual == 'system':
        return

    # =========================================================================
    # 1. Tabla: activos_fijos
    # =========================================================================
    op.execute(sa.text(f"""
        CREATE TABLE {schema_actual}.activos_fijos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL,
            categoria_id UUID NOT NULL,
            codigo_interno VARCHAR(50) NOT NULL,
            descripcion VARCHAR(255) NOT NULL,
            fecha_adquisicion DATE NOT NULL,
            valor_costo NUMERIC(15, 2) NOT NULL,
            valor_residual NUMERIC(15, 2) NOT NULL DEFAULT 0.00,
            tasa_depreciacion_anual_aplicada NUMERIC(5, 2) NOT NULL,
            vida_util_meses_aplicada INTEGER NOT NULL,
            cuenta_gasto_id UUID,
            cuenta_depreciacion_acumulada_id UUID,
            estado VARCHAR(30) NOT NULL DEFAULT 'activo',
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            
            -- Restricciones
            CONSTRAINT chk_activos_fijos_tasa_valida CHECK (tasa_depreciacion_anual_aplicada >= 0 AND tasa_depreciacion_anual_aplicada <= 100),
            
            -- Foreign Keys
            CONSTRAINT fk_activos_fijos_empresa FOREIGN KEY (empresa_id) REFERENCES {schema_actual}.empresas(id),
            CONSTRAINT fk_activos_fijos_categoria FOREIGN KEY (categoria_id) REFERENCES public.categorias_activos_fijos(id),
            CONSTRAINT fk_activos_fijos_cuenta_gasto FOREIGN KEY (cuenta_gasto_id) REFERENCES {schema_actual}.plan_cuentas(id),
            CONSTRAINT fk_activos_fijos_cuenta_dep FOREIGN KEY (cuenta_depreciacion_acumulada_id) REFERENCES {schema_actual}.plan_cuentas(id)
        );
    """))

    op.execute(sa.text(f"""
        CREATE INDEX ix_activos_fijos_empresa_id ON {schema_actual}.activos_fijos(empresa_id);
    """))


    # =========================================================================
    # 2. Tabla: depreciacion_activos
    # =========================================================================
    op.execute(sa.text(f"""
        CREATE TABLE {schema_actual}.depreciacion_activos (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            empresa_id UUID NOT NULL,
            activo_id UUID NOT NULL,
            anio_periodo SMALLINT NOT NULL,
            mes_periodo SMALLINT NOT NULL,
            monto_depreciacion_mes NUMERIC(15, 2) NOT NULL,
            depreciacion_acumulada_hasta_fecha NUMERIC(15, 2) NOT NULL,
            valor_en_libros NUMERIC(15, 2) NOT NULL,
            partida_id UUID,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            
            -- Restricciones
            CONSTRAINT uq_depreciacion_activo_periodo UNIQUE (activo_id, anio_periodo, mes_periodo),
            CONSTRAINT chk_depreciacion_mes_valido CHECK (mes_periodo BETWEEN 1 AND 12),
            
            -- Foreign Keys
            CONSTRAINT fk_depreciacion_activos_empresa FOREIGN KEY (empresa_id) REFERENCES {schema_actual}.empresas(id),
            CONSTRAINT fk_depreciacion_activos_activo FOREIGN KEY (activo_id) REFERENCES {schema_actual}.activos_fijos(id),
            CONSTRAINT fk_depreciacion_activos_partida FOREIGN KEY (partida_id) REFERENCES {schema_actual}.partidas(id)
        );
    """))

    op.execute(sa.text(f"""
        CREATE INDEX idx_depreciacion_activos_empresa_periodo 
        ON {schema_actual}.depreciacion_activos(empresa_id, anio_periodo, mes_periodo);
    """))


def downgrade() -> None:
    # Proteger el esquema 'system' en el rollback
    schema_actual = os.environ.get("TENANT_SCHEMA", "public")
    if schema_actual == 'system':
        return

    # Eliminar en orden inverso al de creación para evitar errores de dependencias de FK
    op.execute(sa.text(f"DROP INDEX IF EXISTS {schema_actual}.idx_depreciacion_activos_empresa_periodo;"))
    op.execute(sa.text(f"DROP TABLE IF EXISTS {schema_actual}.depreciacion_activos;"))

    op.execute(sa.text(f"DROP INDEX IF EXISTS {schema_actual}.ix_activos_fijos_empresa_id;"))
    op.execute(sa.text(f"DROP TABLE IF EXISTS {schema_actual}.activos_fijos;"))