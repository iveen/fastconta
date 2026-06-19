"""chg_diseno_relacion_formularios_sat

Revision ID: 49129fce985b
Revises: 90282f0cefad
Create Date: 2026-06-18 13:10:56.262389

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '49129fce985b'
down_revision: Union[str, None] = '90282f0cefad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def column_exists(conn, table_name, column_name, schema='public'):
    """Verifica si una columna existe usando information_schema"""
    result = conn.execute(sa.text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_schema = :schema 
        AND table_name = :table 
        AND column_name = :column
    """), {"schema": schema, "table": table_name, "column": column_name})
    return result.scalar() is not None


def constraint_exists(conn, table_name, constraint_name, schema='public'):
    """Verifica si un constraint existe usando information_schema"""
    result = conn.execute(sa.text("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_schema = :schema 
        AND table_name = :table 
        AND constraint_name = :name
    """), {"schema": schema, "table": table_name, "name": constraint_name})
    return result.scalar() is not None


def index_exists(conn, index_name, schema='public'):
    """Verifica si un índice existe"""
    result = conn.execute(sa.text("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE schemaname = :schema 
        AND indexname = :name
    """), {"schema": schema, "name": index_name})
    return result.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()
    
    # =========================================================================
    # 1. FORMULARIOS_SAT: Agregar auditoría (si no existe)
    # =========================================================================
    if not column_exists(conn, 'formularios_sat', 'created_at'):
        print("📋 Agregando auditoría a formularios_sat...")
        op.add_column('formularios_sat', 
            sa.Column('created_at', sa.DateTime(timezone=True), 
                     server_default=sa.func.now(), nullable=False),
            schema='public')
        op.add_column('formularios_sat',
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
            schema='public')
        op.add_column('formularios_sat',
            sa.Column('updated_at', sa.DateTime(timezone=True),
                     server_default=sa.func.now(), nullable=True),
            schema='public')
        op.add_column('formularios_sat',
            sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
            schema='public')
        
        op.create_foreign_key('fk_formularios_sat_created_by',
            'formularios_sat', 'users',
            ['created_by'], ['id'],
            source_schema='public', referent_schema='public',
            ondelete='SET NULL')
        op.create_foreign_key('fk_formularios_sat_updated_by',
            'formularios_sat', 'users',
            ['updated_by'], ['id'],
            source_schema='public', referent_schema='public',
            ondelete='SET NULL')
        print("✅ Auditoría agregada a formularios_sat")
    else:
        print("⚠️  Auditoría ya existe en formularios_sat")
    
    # =========================================================================
    # 2. CASILLAS_SAT: Rediseño completo
    # =========================================================================
    
    # 2.1 Dropear constraint único viejo (si existe)
    if constraint_exists(conn, 'casillas_sat', 'uq_casilla_seccion_orden'):
        print("🗑️  Dropeando constraint: uq_casilla_seccion_orden")
        op.drop_constraint('uq_casilla_seccion_orden', 'casillas_sat',
                          schema='public', type_='unique')
    
    # 2.2 Dropear índice viejo (si existe)
    if index_exists(conn, 'idx_casillas_formulario_seccion'):
        print("🗑️  Dropeando índice: idx_casillas_formulario_seccion")
        op.drop_index('idx_casillas_formulario_seccion',
                     table_name='casillas_sat', schema='public')
    
    # 2.3 Dropear FK de formulario_id (si existe)
    if constraint_exists(conn, 'casillas_sat', 'fk_casillas_sat_formulario_id_formula'):
        print("🗑️  Dropeando FK: fk_casillas_sat_formulario_id_formula")
        op.drop_constraint('fk_casillas_sat_formulario_id_formula',
                          'casillas_sat', schema='public', type_='foreignkey')
    
    # 2.4 Dropear columna formulario_id (si existe)
    if column_exists(conn, 'casillas_sat', 'formulario_id'):
        print("🗑️  Dropeando columna: formulario_id")
        op.drop_column('casillas_sat', 'formulario_id', schema='public')
    
    # 2.5 Hacer 'seccion' nullable
    print("📝 Alterando columna 'seccion' a nullable")
    op.alter_column('casillas_sat', 'seccion',
                   existing_type=sa.String(10),
                   nullable=True, schema='public')
    
    # 2.6 Cambiar tipo_casilla de String(20) a String(30)
    print("📝 Alterando tipo_casilla a String(30)")
    op.alter_column('casillas_sat', 'tipo_casilla',
                   existing_type=sa.String(20),
                   type_=sa.String(30),
                   existing_nullable=False,
                   existing_server_default=sa.text("'CALCULO'::character varying"),
                   schema='public')
    
    # 2.7 Agregar seccion_id (si no existe)
    if not column_exists(conn, 'casillas_sat', 'seccion_id'):
        print("📝 Agregando columna: seccion_id")
        op.add_column('casillas_sat',
            sa.Column('seccion_id', postgresql.UUID(as_uuid=True), nullable=True),
            schema='public')
        
        op.create_foreign_key('fk_casillas_sat_seccion',
            'casillas_sat', 'secciones_formulario',
            ['seccion_id'], ['id'],
            source_schema='public', referent_schema='public',
            ondelete='SET NULL')
    
    # 2.8 Agregar nuevos campos de configuración (si no existen)
    nuevos_campos = [
        ('codigo_visual', sa.String(20), None),
        ('descripcion', sa.Text(), None),
        ('naturaleza', sa.String(20), None),
        ('formula_calculo', sa.Text(), None),
        ('porcentaje_aplicable', sa.Numeric(5, 2), None),
        ('campo_origen_factura', sa.String(50), None),
        ('es_editable', sa.Boolean(), sa.text('false')),
        ('requiere_justificacion', sa.Boolean(), sa.text('false')),
        ('es_visible_usuario', sa.Boolean(), sa.text('true'))
    ]
    
    for nombre, tipo, default in nuevos_campos:
        if not column_exists(conn, 'casillas_sat', nombre):
            print(f"📝 Agregando columna: {nombre}")
            if default:
                op.add_column('casillas_sat',
                    sa.Column(nombre, tipo, server_default=default, nullable=True),
                    schema='public')
            else:
                op.add_column('casillas_sat',
                    sa.Column(nombre, tipo, nullable=True),
                    schema='public')
    
    # 2.9 Agregar auditoría (si no existe)
    if not column_exists(conn, 'casillas_sat', 'created_at'):
        print("📋 Agregando auditoría a casillas_sat...")
        op.add_column('casillas_sat',
            sa.Column('created_at', sa.DateTime(timezone=True),
                     server_default=sa.func.now(), nullable=False),
            schema='public')
        op.add_column('casillas_sat',
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
            schema='public')
        op.add_column('casillas_sat',
            sa.Column('updated_at', sa.DateTime(timezone=True),
                     server_default=sa.func.now(), nullable=True),
            schema='public')
        op.add_column('casillas_sat',
            sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
            schema='public')
        
        op.create_foreign_key('fk_casillas_sat_created_by',
            'casillas_sat', 'users',
            ['created_by'], ['id'],
            source_schema='public', referent_schema='public',
            ondelete='SET NULL')
        op.create_foreign_key('fk_casillas_sat_updated_by',
            'casillas_sat', 'users',
            ['updated_by'], ['id'],
            source_schema='public', referent_schema='public',
            ondelete='SET NULL')
    
    # 2.10 Crear constraint único (si no existe)
    if not constraint_exists(conn, 'casillas_sat', 'uq_casilla_seccion_codigo'):
        print("🔒 Creando constraint: uq_casilla_seccion_codigo")
        op.create_unique_constraint('uq_casilla_seccion_codigo',
                                   'casillas_sat',
                                   ['seccion_id', 'codigo'],
                                   schema='public')
    
    # =========================================================================
    # 3. REGIMENES_FORMULARIOS_SAT: Agregar auditoría (si no existe)
    # =========================================================================
    if not column_exists(conn, 'regimenes_formularios_sat', 'created_at'):
        print("📋 Agregando auditoría a regimenes_formularios_sat...")
        op.add_column('regimenes_formularios_sat',
            sa.Column('created_at', sa.DateTime(timezone=True),
                     server_default=sa.func.now(), nullable=False),
            schema='public')
        op.add_column('regimenes_formularios_sat',
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
            schema='public')
        op.add_column('regimenes_formularios_sat',
            sa.Column('updated_at', sa.DateTime(timezone=True),
                     server_default=sa.func.now(), nullable=True),
            schema='public')
        op.add_column('regimenes_formularios_sat',
            sa.Column('updated_by', postgresql.UUID(as_uuid=True), nullable=True),
            schema='public')
        
        op.create_foreign_key('fk_regimenes_formularios_sat_created_by',
            'regimenes_formularios_sat', 'users',
            ['created_by'], ['id'],
            source_schema='public', referent_schema='public',
            ondelete='SET NULL')
        op.create_foreign_key('fk_regimenes_formularios_sat_updated_by',
            'regimenes_formularios_sat', 'users',
            ['updated_by'], ['id'],
            source_schema='public', referent_schema='public',
            ondelete='SET NULL')
        print("✅ Auditoría agregada a regimenes_formularios_sat")
    
    print("\n✅ Migración completada exitosamente")


def downgrade() -> None:
    # =========================================================================
    # 3. REGIMENES_FORMULARIOS_SAT: Revertir auditoría
    # =========================================================================
    op.drop_constraint('fk_regimenes_formularios_sat_updated_by',
                      'regimenes_formularios_sat',
                      schema='public', type_='foreignkey')
    op.drop_constraint('fk_regimenes_formularios_sat_created_by',
                      'regimenes_formularios_sat',
                      schema='public', type_='foreignkey')
    
    op.drop_column('regimenes_formularios_sat', 'updated_by', schema='public')
    op.drop_column('regimenes_formularios_sat', 'updated_at', schema='public')
    op.drop_column('regimenes_formularios_sat', 'created_by', schema='public')
    op.drop_column('regimenes_formularios_sat', 'created_at', schema='public')
    
    # =========================================================================
    # 2. CASILLAS_SAT: Revertir cambios
    # =========================================================================
    op.drop_constraint('uq_casilla_seccion_codigo', 'casillas_sat',
                      schema='public', type_='unique')
    
    op.drop_constraint('fk_casillas_sat_updated_by', 'casillas_sat',
                      schema='public', type_='foreignkey')
    op.drop_constraint('fk_casillas_sat_created_by', 'casillas_sat',
                      schema='public', type_='foreignkey')
    
    op.drop_column('casillas_sat', 'updated_by', schema='public')
    op.drop_column('casillas_sat', 'updated_at', schema='public')
    op.drop_column('casillas_sat', 'created_by', schema='public')
    op.drop_column('casillas_sat', 'created_at', schema='public')
    
    op.drop_column('casillas_sat', 'es_visible_usuario', schema='public')
    op.drop_column('casillas_sat', 'requiere_justificacion', schema='public')
    op.drop_column('casillas_sat', 'es_editable', schema='public')
    op.drop_column('casillas_sat', 'campo_origen_factura', schema='public')
    op.drop_column('casillas_sat', 'porcentaje_aplicable', schema='public')
    op.drop_column('casillas_sat', 'formula_calculo', schema='public')
    op.drop_column('casillas_sat', 'naturaleza', schema='public')
    op.drop_column('casillas_sat', 'descripcion', schema='public')
    op.drop_column('casillas_sat', 'codigo_visual', schema='public')
    
    op.drop_constraint('fk_casillas_sat_seccion', 'casillas_sat',
                      schema='public', type_='foreignkey')
    op.drop_column('casillas_sat', 'seccion_id', schema='public')
    
    op.alter_column('casillas_sat', 'tipo_casilla',
                   existing_type=sa.String(30),
                   type_=sa.String(20),
                   existing_nullable=False,
                   existing_server_default=sa.text("'CALCULO'::character varying"),
                   schema='public')
    
    op.alter_column('casillas_sat', 'seccion',
                   existing_type=sa.String(10),
                   nullable=False, schema='public')
    
    op.create_unique_constraint('uq_casilla_seccion_orden', 'casillas_sat',
                               ['formulario_id', 'seccion', 'orden_seccion'],
                               schema='public')
    
    op.add_column('casillas_sat',
        sa.Column('formulario_id', postgresql.UUID(as_uuid=True), nullable=False),
        schema='public')
    
    op.create_foreign_key('fk_casillas_sat_formulario_id_formula',
        'casillas_sat', 'formularios_sat',
        ['formulario_id'], ['id'],
        source_schema='public', referent_schema='public')
    
    # =========================================================================
    # 1. FORMULARIOS_SAT: Revertir auditoría
    # =========================================================================
    op.drop_constraint('fk_formularios_sat_updated_by', 'formularios_sat',
                      schema='public', type_='foreignkey')
    op.drop_constraint('fk_formularios_sat_created_by', 'formularios_sat',
                      schema='public', type_='foreignkey')
    
    op.drop_column('formularios_sat', 'updated_by', schema='public')
    op.drop_column('formularios_sat', 'updated_at', schema='public')
    op.drop_column('formularios_sat', 'created_by', schema='public')
    op.drop_column('formularios_sat', 'created_at', schema='public')