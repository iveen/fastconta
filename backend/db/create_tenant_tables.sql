-- Tablas de negocio para un tenant

CREATE TABLE IF NOT EXISTS {schema}.empresas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    nit VARCHAR(20) UNIQUE NOT NULL,
    direccion TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.plan_cuentas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(255) NOT NULL,
    tipo VARCHAR(20) NOT NULL,
    naturaleza VARCHAR(10) NOT NULL,
    acepta_tercero BOOLEAN DEFAULT FALSE,
    nivel INTEGER DEFAULT 1,
    cuenta_padre_id UUID,
    activa BOOLEAN DEFAULT TRUE,
    empresa_id UUID NOT NULL REFERENCES {schema}.empresas(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE SEQUENCE IF NOT EXISTS {schema}.partidas_numero_seq;

CREATE TABLE IF NOT EXISTS {schema}.partidas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    numero INTEGER NOT NULL DEFAULT nextval('{schema}.partidas_numero_seq') UNIQUE,
    numero_poliza VARCHAR(50) UNIQUE,
    fecha DATE NOT NULL,
    descripcion TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.detalle_partidas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    partida_id UUID NOT NULL REFERENCES {schema}.partidas(id) ON DELETE CASCADE,
    cuenta_id UUID NOT NULL REFERENCES {schema}.plan_cuentas(id),
    tipo_movimiento VARCHAR(10) NOT NULL,
    monto NUMERIC(12,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS {schema}.secuencias (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    entidad VARCHAR(50) NOT NULL,
    empresa_id UUID NOT NULL REFERENCES {schema}.empresas(id),
    contador INTEGER DEFAULT 1,
    UNIQUE(entidad, empresa_id)
);

CREATE TABLE IF NOT EXISTS {schema}.periodos_fiscales (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    cerrado BOOLEAN NOT NULL DEFAULT FALSE,
    empresa_id UUID NOT NULL REFERENCES {schema}.empresas(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS {schema}.facturas_electronicas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    empresa_id UUID NOT NULL REFERENCES tenant_contaguate.empresas(id),
    xml_original TEXT NOT NULL,
    numero_autorizacion VARCHAR(50) NOT NULL,
    autorizacion_uuid VARCHAR(50),
    serie VARCHAR(20),
    numero VARCHAR(20) NOT NULL,
    tipo_documento VARCHAR(10),
    moneda VARCHAR(5),
    fecha_emision TIMESTAMPTZ NOT NULL,
    emisor_nit VARCHAR(15) NOT NULL,
    emisor_nombre VARCHAR(255) NOT NULL,
    receptor_nit VARCHAR(15) NOT NULL,
    receptor_nombre VARCHAR(255) NOT NULL,
    total_gravado NUMERIC(12,2) DEFAULT 0,
    total_iva NUMERIC(12,2) DEFAULT 0,
    total_exento NUMERIC(12,2) DEFAULT 0,
    total NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
-- Repite para los otros esquemas cambiando el nombre del schema

-- Historial de Alembic
CREATE TABLE IF NOT EXISTS {schema}.alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);
INSERT INTO {schema}.alembic_version (version_num) VALUES ('d90dd406e3ad') ON CONFLICT DO NOTHING;