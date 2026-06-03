"""add: codigo a tipo de libro

Revision ID: c46f6e9c812f
Revises: 0f2c4f1bfb0d
Create Date: 2026-06-03 10:48:44.521595

"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = 'c46f6e9c812f'
down_revision: Union[str, None] = '0f2c4f1bfb0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    1. Amplía el campo nombre de VARCHAR(50) a VARCHAR(255)
    2. Agrega el campo codigo VARCHAR(50) NOT NULL UNIQUE
    3. Inserta los registros semilla (compras, ventas)
    """
    
    conn = op.get_bind()
    
    print("🔄 Procesando tabla public.tipos_libro")
    
    # 1. Ampliar campo nombre de 50 a 255 caracteres
    conn.execute(text("""
        ALTER TABLE public.tipos_libro 
        ALTER COLUMN nombre TYPE VARCHAR(255)
    """))
    
    # 2. Agregar columna codigo (primero nullable para permitir datos existentes)
    conn.execute(text("""
        ALTER TABLE public.tipos_libro 
        ADD COLUMN IF NOT EXISTS codigo VARCHAR(50)
    """))
    
    # 3. Verificar si ya existen registros
    result = conn.execute(text("""
        SELECT COUNT(*) FROM public.tipos_libro
    """))
    count = result.scalar()
    
    if count == 0:
        # 4. Insertar registros semilla
        conn.execute(text("""
            INSERT INTO public.tipos_libro (id, nombre, codigo) 
            VALUES 
                (gen_random_uuid(), 'Libro de Compras', 'compras'),
                (gen_random_uuid(), 'Libro de Ventas', 'ventas')
        """))
        print("  ✅ Registros semilla insertados")
    else:
        # Si ya hay registros pero no tienen codigo, actualizar los conocidos
        conn.execute(text("""
            UPDATE public.tipos_libro 
            SET codigo = 'compras' 
            WHERE LOWER(nombre) LIKE '%compra%' AND (codigo IS NULL OR codigo = '')
        """))
        conn.execute(text("""
            UPDATE public.tipos_libro 
            SET codigo = 'ventas' 
            WHERE LOWER(nombre) LIKE '%venta%' AND (codigo IS NULL OR codigo = '')
        """))
        print(f"  ⚠️  Ya existían {count} registros. Se actualizaron códigos conocidos.")
    
    # 5. Hacer la columna codigo NOT NULL y UNIQUE
    # Primero eliminar valores NULL si quedaron (por seguridad)
    conn.execute(text("""
        UPDATE public.tipos_libro 
        SET codigo = LOWER(REPLACE(nombre, ' ', '_'))
        WHERE codigo IS NULL OR codigo = ''
    """))
    
    # Ahora aplicar las restricciones
    conn.execute(text("""
        ALTER TABLE public.tipos_libro 
        ALTER COLUMN codigo SET NOT NULL
    """))
    
    # Agregar constraint UNIQUE (con nombre explícito para poder eliminarlo en downgrade)
    conn.execute(text("""
        ALTER TABLE public.tipos_libro 
        ADD CONSTRAINT uq_tipos_libro_codigo UNIQUE (codigo)
    """))
    
    print("  ✅ Tabla public.tipos_libro actualizada correctamente")


def downgrade() -> None:
    """
    Revierte los cambios:
    1. Elimina constraint UNIQUE de codigo
    2. Elimina la columna codigo
    3. Reduce nombre de 255 a 50 caracteres
    4. Elimina los registros semilla (compras, ventas)
    """
    conn = op.get_bind()
    
    print("🔄 Revirtiendo cambios en public.tipos_libro")
    
    try:
        # 1. Eliminar constraint UNIQUE
        conn.execute(text("""
            ALTER TABLE public.tipos_libro 
            DROP CONSTRAINT IF EXISTS uq_tipos_libro_codigo
        """))
        
        # 2. Eliminar columna codigo
        conn.execute(text("""
            ALTER TABLE public.tipos_libro 
            DROP COLUMN IF EXISTS codigo
        """))
        
        # 3. Reducir nombre de 255 a 50 caracteres
        # Primero truncar valores que excedan 50 chars para evitar errores
        conn.execute(text("""
            UPDATE public.tipos_libro 
            SET nombre = LEFT(nombre, 50)
            WHERE LENGTH(nombre) > 50
        """))
        
        conn.execute(text("""
            ALTER TABLE public.tipos_libro 
            ALTER COLUMN nombre TYPE VARCHAR(50)
        """))
        
        # 4. Eliminar registros semilla (opcional, según prefieras)
        conn.execute(text("""
            DELETE FROM public.tipos_libro 
            WHERE codigo IN ('compras', 'ventas')
        """))
        
        print("  ✅ Tabla public.tipos_libro revertida correctamente")
        
    except Exception as e:
        print(f"  ❌ Error revirtiendo cambios: {e}")
        raise
