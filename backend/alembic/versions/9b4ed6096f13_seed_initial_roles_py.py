"""seed_initial_roles.py

Revision ID: 9b4ed6096f13
Revises: 22cc9e33a26f
Create Date: 2026-07-07 09:48:22.363213

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '9b4ed6096f13'
down_revision: Union[str, None] = '22cc9e33a26f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """
    Inserta los roles base del sistema.
    Estos roles son inmutables y necesarios para el bootstrap.
    """
    op.execute("""
        INSERT INTO public.roles (codigo, nombre, descripcion, nivel_acceso, public_id, is_active, created_at)
        VALUES 
            ('superadmin', 'Super Administrador', 
             'Acceso total al sistema. Gestiona tenants, usuarios globales y configuración del sistema.', 
             100, gen_random_uuid(), true, NOW()),
            ('tenant_manager', 'Administrador de Tenant', 
             'Administra un tenant específico y sus usuarios. Acceso completo dentro de su tenant.', 
             80, gen_random_uuid(), true, NOW()),
            ('tenant_member', 'Miembro de Tenant', 
             'Contador con acceso operativo dentro del tenant. Puede crear partidas, gestionar facturas.', 
             60, gen_random_uuid(), true, NOW()),
            ('tenant_client', 'Cliente de Tenant', 
             'Cliente final con acceso de solo lectura a reportes y declaraciones.', 
             20, gen_random_uuid(), true, NOW())
        ON CONFLICT (codigo) DO NOTHING;
    """)
    
    # Verificación
    op.execute("""
        DO $$ 
        DECLARE
            role_count INT;
        BEGIN
            SELECT COUNT(*) INTO role_count FROM public.roles WHERE codigo IN 
                ('superadmin', 'tenant_manager', 'tenant_member', 'tenant_client');
            IF role_count != 4 THEN
                RAISE EXCEPTION 'Error: Se esperaban 4 roles, pero se encontraron %', role_count;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """
    Elimina los roles base.
    ADVERTENCIA: Esto fallará si existen usuarios con estos roles.
    """
    op.execute("""
        DELETE FROM public.roles 
        WHERE codigo IN ('superadmin', 'tenant_manager', 'tenant_member', 'tenant_client')
        AND id NOT IN (SELECT DISTINCT role_id FROM public.users);
    """)
