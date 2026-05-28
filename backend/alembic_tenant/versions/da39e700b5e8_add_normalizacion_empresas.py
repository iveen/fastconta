"""add: normalizacion Empresas

Revision ID: da39e700b5e8
Revises: 9e09153f8cc1
Create Date: 2026-05-27 21:04:35.717112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision: str = 'da39e700b5e8'
down_revision: Union[str, None] = '9e09153f8cc1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    
    # 1. Crear tablas nuevas
    op.create_table('domicilios',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('empresa_id', sa.UUID(), nullable=False),
        sa.Column('tipo_domicilio_id', sa.UUID(), nullable=False),
        sa.Column('departamento_id', sa.UUID(), nullable=False),
        sa.Column('municipio_id', sa.UUID(), nullable=False),
        sa.Column('direccion_exacta', sa.String(length=255), nullable=False),
        sa.Column('zona', sa.String(length=10), nullable=True),
        sa.Column('codigo_postal', sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(['departamento_id'], ['public.departamentos.id'], name=op.f('fk_domicilios_departamento_id_departamentos')),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_domicilios_empresa_id_empresas')),
        sa.ForeignKeyConstraint(['municipio_id'], ['public.municipios.id'], name=op.f('fk_domicilios_municipio_id_municipios')),
        sa.ForeignKeyConstraint(['tipo_domicilio_id'], ['public.tipos_domicilio.id'], name=op.f('fk_domicilios_tipo_domicilio_id_tipos_domicilio')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_domicilios'))
    )

    op.create_table('representantes_legales',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('empresa_id', sa.UUID(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('dpi', sa.String(length=20), nullable=False),
        sa.Column('fecha_nombramiento', sa.Date(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('es_activo', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['empresa_id'], ['empresas.id'], name=op.f('fk_representantes_legales_empresa_id_empresas')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_representantes_legales'))
    )

    # 2. Seed global
    op.execute("""
        INSERT INTO public.regimenes_fiscales (id, nombre) 
        VALUES (gen_random_uuid(), 'NORMAL') ON CONFLICT DO NOTHING;
        INSERT INTO public.tipos_persona (id, nombre) 
        VALUES (gen_random_uuid(), 'NATURAL') ON CONFLICT DO NOTHING;
    """)

    # 3. Preparar empresas (Agregar columnas NULLABLE primero)
    with op.batch_alter_table('empresas') as batch_op:
        batch_op.add_column(sa.Column('nombre_comercial', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('regimen_fiscal_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('tipo_persona_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default='true'))

    # 4. Patch datos empresas
    op.execute("""
        UPDATE empresas SET 
            nombre_comercial = 'N/A',
            regimen_fiscal_id = (SELECT id FROM public.regimenes_fiscales LIMIT 1),
            tipo_persona_id = (SELECT id FROM public.tipos_persona LIMIT 1)
        WHERE regimen_fiscal_id IS NULL;
    """)
    
    # 5. Convertir empresas a NOT NULL y crear FKs
    with op.batch_alter_table('empresas') as batch_op:
        batch_op.alter_column('nombre_comercial', nullable=False)
        batch_op.alter_column('regimen_fiscal_id', nullable=False)
        batch_op.alter_column('tipo_persona_id', nullable=False)
    
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_empresas_tipo_persona') THEN
                ALTER TABLE empresas ADD CONSTRAINT fk_empresas_tipo_persona FOREIGN KEY (tipo_persona_id) REFERENCES public.tipos_persona (id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_empresas_regimen_fiscal') THEN
                ALTER TABLE empresas ADD CONSTRAINT fk_empresas_regimen_fiscal FOREIGN KEY (regimen_fiscal_id) REFERENCES public.regimenes_fiscales (id);
            END IF;
        END $$;
    """)

    # 6. Preparar sat_libros (Agregar columnas NULLABLE)
    with op.batch_alter_table('sat_libros') as batch_op:
        batch_op.add_column(sa.Column('tipo_libro_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('regimen_fiscal_id', sa.UUID(), nullable=True))
        batch_op.add_column(sa.Column('estado_id', sa.UUID(), nullable=True))

    # 6.5. EMERGENCIA: Asegurar que existan catálogos antes del UPDATE
    op.execute("""
        INSERT INTO public.tipos_libro (id, nombre) VALUES (gen_random_uuid(), 'GENERAL') ON CONFLICT DO NOTHING;
        INSERT INTO public.estados_libro (id, nombre) VALUES (gen_random_uuid(), 'BORRADOR') ON CONFLICT DO NOTHING;
    """)

    # 7. Patch datos sat_libros (Más robusto)
    # Si sigue fallando, es porque no hay NADA en las tablas de la base de datos.
    op.execute("""
        UPDATE sat_libros SET 
            tipo_libro_id = (SELECT id FROM public.tipos_libro LIMIT 1),
            regimen_fiscal_id = (SELECT id FROM public.regimenes_fiscales LIMIT 1),
            estado_id = (SELECT id FROM public.estados_libro LIMIT 1)
        WHERE tipo_libro_id IS NULL;
    """)
    # 8. Convertir sat_libros a NOT NULL
    with op.batch_alter_table('sat_libros') as batch_op:
        batch_op.alter_column('tipo_libro_id', nullable=False)
        batch_op.alter_column('regimen_fiscal_id', nullable=False)
        batch_op.alter_column('estado_id', nullable=False)

    # 9. Crear constraints y limpiar sat_libros
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_sat_libros_tipo_libro') THEN
                ALTER TABLE sat_libros ADD CONSTRAINT fk_sat_libros_tipo_libro FOREIGN KEY (tipo_libro_id) REFERENCES public.tipos_libro (id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_sat_libros_regimen') THEN
                ALTER TABLE sat_libros ADD CONSTRAINT fk_sat_libros_regimen FOREIGN KEY (regimen_fiscal_id) REFERENCES public.regimenes_fiscales (id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_sat_libros_estado') THEN
                ALTER TABLE sat_libros ADD CONSTRAINT fk_sat_libros_estado FOREIGN KEY (estado_id) REFERENCES public.estados_libro (id);
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN 
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'uq_sat_libros_periodo'
            ) THEN
                ALTER TABLE sat_libros 
                ADD CONSTRAINT uq_sat_libros_periodo 
                UNIQUE (empresa_id, tipo_libro_id, regimen_fiscal_id, anio_periodo, mes_periodo);
            END IF;
        END $$;
    """)

    with op.batch_alter_table('sat_libros') as batch_op:
        batch_op.drop_column('tipo_libro')
        batch_op.drop_column('regimen_fiscal')
        batch_op.drop_column('estado')


def downgrade() -> None:
    tenant_schema = os.environ.get("TENANT_SCHEMA", "public")
    if tenant_schema == 'system':
        return
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('sat_libros', schema=None) as batch_op:
        batch_op.add_column(sa.Column('tipo_libro', sa.VARCHAR(length=7), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('regimen_fiscal', sa.VARCHAR(length=21), autoincrement=False, nullable=False))
        batch_op.add_column(sa.Column('estado', sa.VARCHAR(length=10), server_default=sa.text("'borrador'::character varying"), autoincrement=False, nullable=False))
        try:
            batch_op.drop_constraint(batch_op.f('fk_sat_libros_tipo_libro_id_tipos_libro'), type_='foreignkey')
        except:
            pass
        try:
            batch_op.drop_constraint(batch_op.f('fk_sat_libros_estado_id_estados_libro'), type_='foreignkey')
        except:
            pass
        try:
            batch_op.drop_constraint(batch_op.f('fk_sat_libros_regimen_fiscal_id_regimenes_fiscales'), type_='foreignkey')
        except:
            pass
        try:
            batch_op.drop_constraint('uq_sat_libros_periodo', type_='unique')
        except:
            pass
        batch_op.create_unique_constraint('uq_sat_libros_periodo', ['empresa_id', 'tipo_libro', 'anio_periodo', 'mes_periodo'])
        try:
            batch_op.drop_column('estado_id')
        except:
            pass
        try:
            batch_op.drop_column('regimen_fiscal_id')
        except:
            pass
        try:
            batch_op.drop_column('tipo_libro_id')
        except:
            pass

    with op.batch_alter_table('partidas', schema=None) as batch_op:
        try:
            batch_op.drop_constraint(batch_op.f('uq_partidas_numero'), type_='unique')
        except:
            pass
        batch_op.create_unique_constraint('partidas_numero_key', ['numero'])

    with op.batch_alter_table('facturas_impuestos_especiales', schema=None) as batch_op:
        try:
            batch_op.drop_constraint(batch_op.f('fk_facturas_impuestos_especiales_catalogo_id_catalogo_impuestos_especiales'), type_='foreignkey')
        except:
            pass
        batch_op.create_foreign_key('facturas_impuestos_especiales_catalogo_id_fkey', 'catalogo_impuestos_especiales', ['catalogo_id'], ['id'])

    with op.batch_alter_table('facturas_electronicas', schema=None) as batch_op:
        try:
            batch_op.drop_constraint(batch_op.f('fk_facturas_electronicas_tipo_documento_id_tipos_dte'), type_='foreignkey')
        except:
            pass
        try:
            batch_op.drop_constraint(batch_op.f('fk_facturas_electronicas_moneda_id_catalogo_monedas'), type_='foreignkey')
        except:
            pass
        batch_op.create_foreign_key('facturas_electronicas_moneda_id_fkey', 'catalogo_monedas', ['moneda_id'], ['id'])
        batch_op.create_foreign_key('facturas_electronicas_tipo_documento_id_fkey', 'tipos_dte', ['tipo_documento_id'], ['id'])

    with op.batch_alter_table('empresas', schema=None) as batch_op:
        try:
            batch_op.drop_constraint(batch_op.f('fk_empresas_regimen_fiscal_id_regimenes_fiscales'), type_='foreignkey')
        except:
            pass
        try:
            batch_op.drop_constraint(batch_op.f('fk_empresas_tipo_persona_id_tipos_persona'), type_='foreignkey')
        except:
            pass
        try:
            batch_op.drop_constraint(batch_op.f('uq_empresas_nit'), type_='unique')
        except:
            pass
        batch_op.create_unique_constraint('empresas_nit_key', ['nit'])
        try:
            batch_op.drop_column('is_active')
        except:
            pass
        try:
            batch_op.drop_column('tipo_persona_id')
        except:
            pass
        try:
            batch_op.drop_column('regimen_fiscal_id')
        except:
            pass
        try:
            batch_op.drop_column('nombre_comercial')
        except:
            pass
    try:
        op.drop_table('representantes_legales')
    except:
        pass
    try:
        op.drop_table('domicilios')
    except:
        pass
    # ### end Alembic commands ###
