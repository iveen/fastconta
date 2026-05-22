SET search_path TO tenant_servicios_contables;

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
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

-- Para tenant_firmapérez
INSERT INTO alembic_version (version_num) VALUES ('ecac85d2eec2')
ON CONFLICT (version_num) DO NOTHING;

GRANT ALL ON SCHEMA tenant_servicios_contables TO fastconta_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA tenant_servicios_contables GRANT ALL ON TABLES TO fastconta_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA tenant_servicios_contables GRANT ALL ON SEQUENCES TO fastconta_user;


-- tenant_contaguate
DO $$
DECLARE r RECORD;
BEGIN
  FOR r IN SELECT tablename FROM pg_tables WHERE schemaname = 'tenant_servicios_contables'
  LOOP
    EXECUTE 'ALTER TABLE tenant_servicios_contables.' || r.tablename || ' OWNER TO fastconta_user';
  END LOOP;
  FOR r IN SELECT sequencename FROM pg_sequences WHERE schemaname = 'tenant_servicios_contables'
  LOOP
    EXECUTE 'ALTER SEQUENCE tenant_servicios_contables.' || r.sequencename || ' OWNER TO fastconta_user';
  END LOOP;
END $$;

-- Repite para tenant_firmapérez y tenant_servicios_contables cambiando el nombre del schema.

--- UPDATE tenant_contaguate.plan_cuentas SET activa = false WHERE codigo = '1.1.1';

--- UPDATE tenant_contaguate.periodos_fiscales SET cerrado = false WHERE nombre = '2026';

