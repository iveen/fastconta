"""create: catalogo dte y monedas ISO

Revision ID: 873a7d9ea9d4
Revises: 66a2697e7db8
Create Date: 2026-05-25 15:39:52.741545

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers, used by Alembic.
revision: str = '873a7d9ea9d4'
down_revision: Union[str, None] = '66a2697e7db8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # ==========================================
    # TABLA: tipos_dte (Global - schema public)
    # ==========================================
    op.create_table(
        'tipos_dte',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('codigo', sa.String(10), unique=True, nullable=False, index=True),
        sa.Column('descripcion', sa.String(100), nullable=False),
        sa.Column('requiere_complemento', sa.Boolean, default=False, nullable=False),
        sa.Column('es_factura', sa.Boolean, default=True, nullable=False),
        sa.Column('activo', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        schema='public'
    )

    # Seed inicial: Tipos DTE soportados en FEL Guatemala
    tipos_dte_data = [
        {'codigo': 'FACT', 'descripcion': 'Factura Electrónica', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FCAM', 'descripcion': 'Factura Cambiaria', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FPEQ', 'descripcion': 'Factura Pequeño Contribuyente', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FCAP', 'descripcion': 'Factura Cambiaria Pequeño Contribuyente', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FESP', 'descripcion': 'Factura Especial', 'requiere_complemento': True, 'es_factura': True},
        {'codigo': 'NABN', 'descripcion': 'Nota de Abono', 'requiere_complemento': True, 'es_factura': False},
        {'codigo': 'RDON', 'descripcion': 'Recibo de Donación', 'requiere_complemento': False, 'es_factura': False},
        {'codigo': 'RECI', 'descripcion': 'Recibo', 'requiere_complemento': False, 'es_factura': False},
        {'codigo': 'NDEB', 'descripcion': 'Nota de Débito', 'requiere_complemento': True, 'es_factura': False},
        {'codigo': 'NCRE', 'descripcion': 'Nota de Crédito', 'requiere_complemento': True, 'es_factura': False},
        {'codigo': 'FACA', 'descripcion': 'Factura Contribuyente Agropecuario', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FCCA', 'descripcion': 'Factura Cambiaria Contribuyente Agropecuario', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FAPE', 'descripcion': 'Factura Pequeño Contribuyente Régimen Electrónico', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FAAE', 'descripcion': 'Factura Agropecuario Régimen Electrónico Especial', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FCAE', 'descripcion': 'Factura Cambiaria Agropecuario Régimen Electrónico Especial', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'CIVA', 'descripcion': 'Constancia de Exención de IVA', 'requiere_complemento': False, 'es_factura': False},
        {'codigo': 'CAIS', 'descripcion': 'Constancia de Adquisición de Insumos y Servicios', 'requiere_complemento': False, 'es_factura': False},
        {'codigo': 'NEV', 'descripcion': 'Nota de Envío', 'requiere_complemento': False, 'es_factura': False},
        {'codigo': 'RANT', 'descripcion': 'Recibo de Anticipo', 'requiere_complemento': False, 'es_factura': False},
        {'codigo': 'FACP', 'descripcion': 'Factura Provisional', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FEPE', 'descripcion': 'Factura Específica', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FARP', 'descripcion': 'Factura Contribuyente Régimen Primario', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FCRP', 'descripcion': 'Factura Cambiaria Contribuyente Régimen Primario', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FPEC', 'descripcion': 'Factura Contribuyente Régimen Pecuario', 'requiere_complemento': False, 'es_factura': True},
        {'codigo': 'FCPC', 'descripcion': 'Factura Cambiaria Contribuyente Régimen Pecuario', 'requiere_complemento': False, 'es_factura': True},
    ]

    op.bulk_insert(
        sa.table('tipos_dte',
            sa.column('id', postgresql.UUID(as_uuid=True)),
            sa.column('codigo', sa.String),
            sa.column('descripcion', sa.String),
            sa.column('requiere_complemento', sa.Boolean),
            sa.column('es_factura', sa.Boolean),
            sa.column('activo', sa.Boolean),
        ),
        [
            {
                'id': uuid.uuid4(),
                'codigo': t['codigo'],
                'descripcion': t['descripcion'],
                'requiere_complemento': t['requiere_complemento'],
                'es_factura': t['es_factura'],
                'activo': True
            } for t in tipos_dte_data
        ]
    )

    # ==========================================
    # TABLA: catalogo_monedas (Global - schema public)
    # ==========================================
    op.create_table(
        'catalogo_monedas',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('codigo_banguat', sa.String(5), unique=True, nullable=False, index=True),
        sa.Column('codigo_iso', sa.String(3), unique=True, nullable=False, index=True),
        sa.Column('nombre', sa.String(50), nullable=False),
        sa.Column('simbolo', sa.String(5), nullable=True),
        sa.Column('decimales', sa.Integer, default=2, nullable=False),
        sa.Column('activo', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        schema='public'
    )

    # Seed inicial: Monedas oficiales del Banco de Guatemala (PDF codmonedas.pdf)
    monedas_data = [
        {'codigo_banguat': '01', 'codigo_iso': 'GTQ', 'nombre': 'Quetzal', 'simbolo': 'Q', 'decimales': 2},
        {'codigo_banguat': '02', 'codigo_iso': 'USD', 'nombre': 'Dólar Estadounidense', 'simbolo': '$', 'decimales': 2},
        {'codigo_banguat': '03', 'codigo_iso': 'JPY', 'nombre': 'Yen', 'simbolo': '¥', 'decimales': 0},
        {'codigo_banguat': '05', 'codigo_iso': 'CHF', 'nombre': 'Franco Suizo', 'simbolo': 'CHF', 'decimales': 2},
        {'codigo_banguat': '07', 'codigo_iso': 'CAD', 'nombre': 'Dólar Canadiense', 'simbolo': 'C$', 'decimales': 2},
        {'codigo_banguat': '09', 'codigo_iso': 'GBP', 'nombre': 'Libra Esterlina', 'simbolo': '£', 'decimales': 2},
        {'codigo_banguat': '15', 'codigo_iso': 'SEK', 'nombre': 'Corona Sueca', 'simbolo': 'kr', 'decimales': 2},
        {'codigo_banguat': '16', 'codigo_iso': 'CRC', 'nombre': 'Colón Costarricense', 'simbolo': '₡', 'decimales': 2},
        {'codigo_banguat': '18', 'codigo_iso': 'MXN', 'nombre': 'Peso Mexicano', 'simbolo': '$', 'decimales': 2},
        {'codigo_banguat': '19', 'codigo_iso': 'HNL', 'nombre': 'Lempira', 'simbolo': 'L', 'decimales': 2},
        {'codigo_banguat': '20', 'codigo_iso': 'DKK', 'nombre': 'Corona Danesa', 'simbolo': 'kr', 'decimales': 2},
        {'codigo_banguat': '21', 'codigo_iso': 'NIO', 'nombre': 'Córdoba Oro', 'simbolo': 'C$', 'decimales': 2},
        {'codigo_banguat': '22', 'codigo_iso': 'VED', 'nombre': 'Bolívar Soberano', 'simbolo': 'Bs', 'decimales': 2},
        {'codigo_banguat': '27', 'codigo_iso': 'AUD', 'nombre': 'Dólar Australiano', 'simbolo': 'A$', 'decimales': 2},
        {'codigo_banguat': '28', 'codigo_iso': 'EUR', 'nombre': 'Euro', 'simbolo': '€', 'decimales': 2},
    ]

    op.bulk_insert(
        sa.table('catalogo_monedas',
            sa.column('id', postgresql.UUID(as_uuid=True)),
            sa.column('codigo_banguat', sa.String),
            sa.column('codigo_iso', sa.String),
            sa.column('nombre', sa.String),
            sa.column('simbolo', sa.String),
            sa.column('decimales', sa.Integer),
            sa.column('activo', sa.Boolean),
        ),
        [
            {
                'id': uuid.uuid4(),
                'codigo_banguat': m['codigo_banguat'],
                'codigo_iso': m['codigo_iso'],
                'nombre': m['nombre'],
                'simbolo': m['simbolo'],
                'decimales': m['decimales'],
                'activo': True
            } for m in monedas_data
        ]
    )

def downgrade() -> None:
    op.drop_table('catalogo_monedas', schema='public')
    op.drop_table('tipos_dte', schema='public')