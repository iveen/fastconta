# migrations/public/add_catalogos_declaraciones_sat_public.py

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = 'public_001' # Ajusta según tu convención
down_revision: Union[str, None] = 'b89a23627bb9' # ⚠️ Apunta al head de tu ramal PÚBLICO
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Catálogo de Formularios SAT
    op.create_table(
        'formularios_sat',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('codigo', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('descripcion', sa.Text, nullable=True),
        schema='public'
    )

    # 2. Catálogo de Casillas SAT
    op.create_table(
        'casillas_sat',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('formulario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public.formularios_sat.id'), nullable=False),
        sa.Column('seccion', sa.String(10), nullable=False),
        sa.Column('codigo', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('nombre', sa.String(255), nullable=False),
        sa.Column('tipo_valor', sa.String(20), nullable=False),
        sa.Column('orden', sa.Integer, server_default='0'),
        schema='public'
    )

    # 3. Tabla Puente: Regímenes <-> Formularios
    op.create_table(
        'regimenes_formularios_sat',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('regimen_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public.regimenes_fiscales.id'), nullable=False),
        sa.Column('formulario_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('public.formularios_sat.id'), nullable=False),
        sa.Column('es_obligatorio', sa.Boolean, server_default='true', nullable=False),
        sa.UniqueConstraint('regimen_id', 'formulario_id', name='uq_regimen_formulario'),
        schema='public'
    )

def downgrade() -> None:
    op.drop_table('regimenes_formularios_sat', schema='public')
    op.drop_table('casillas_sat', schema='public')
    op.drop_table('formularios_sat', schema='public')