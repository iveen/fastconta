SET search_path TO tenant_firmapérez;

-- Crear tabla empresas
CREATE TABLE IF NOT EXISTS empresas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    nit VARCHAR(20) UNIQUE NOT NULL,
    direccion TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Crear tabla plan_cuentas
CREATE TABLE IF NOT EXISTS plan_cuentas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    naturaleza VARCHAR(10) NOT NULL,
    acepta_tercero BOOLEAN DEFAULT FALSE,
    nivel INTEGER DEFAULT 1,
    cuenta_padre_id UUID,
    activa BOOLEAN DEFAULT TRUE,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Crear secuencia para número de partida
CREATE SEQUENCE IF NOT EXISTS partidas_numero_seq;

-- Crear tabla partidas
CREATE TABLE IF NOT EXISTS partidas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    numero INTEGER NOT NULL DEFAULT nextval('partidas_numero_seq') UNIQUE,
    numero_poliza VARCHAR(50) UNIQUE,
    fecha DATE NOT NULL,
    descripcion TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Crear tabla detalle_partidas
CREATE TABLE IF NOT EXISTS detalle_partidas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    partida_id UUID NOT NULL REFERENCES partidas(id) ON DELETE CASCADE,
    cuenta_id UUID NOT NULL REFERENCES plan_cuentas(id),
    tipo_movimiento VARCHAR(10) NOT NULL,
    monto NUMERIC(12,2) NOT NULL
);

-- Crear tabla secuencias
CREATE TABLE IF NOT EXISTS secuencias (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entidad VARCHAR(50) NOT NULL,
    empresa_id UUID NOT NULL REFERENCES empresas(id),
    contador INTEGER DEFAULT 1,
    UNIQUE(entidad, empresa_id)
);

-- Crear tabla periodos_fiscales
CREATE TABLE IF NOT EXISTS periodos_fiscales (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    cerrado BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Para tenant_contaguate
CREATE TABLE IF NOT EXISTS tenant_contaguate.alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Para tenant_firmapérez
CREATE TABLE IF NOT EXISTS tenant_firmapérez.alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Para tenant_contaguate
INSERT INTO tenant_contaguate.alembic_version (version_num) VALUES ('d90dd406e3ad')
ON CONFLICT (version_num) DO NOTHING;

-- Para tenant_firmapérez
INSERT INTO tenant_firmapérez.alembic_version (version_num) VALUES ('d90dd406e3ad')
ON CONFLICT (version_num) DO NOTHING;


UPDATE tenant_contaguate.plan_cuentas SET activa = false WHERE codigo = '1.1.1';
