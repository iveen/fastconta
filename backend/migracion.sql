BEGIN;

CREATE TABLE tenant_servicios_contables.alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 00f9b652f015

CREATE TABLE tenant_servicios_contables.empresas (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    nombre VARCHAR(255) NOT NULL, 
    nit VARCHAR(20) NOT NULL, 
    direccion TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    UNIQUE (nit)
);

CREATE TABLE tenant_servicios_contables.plan_cuentas (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    codigo VARCHAR(20) NOT NULL, 
    nombre VARCHAR(255) NOT NULL, 
    tipo VARCHAR(20) NOT NULL, 
    naturaleza VARCHAR(10) NOT NULL, 
    acepta_tercero BOOLEAN, 
    nivel INTEGER, 
    cuenta_padre_id UUID, 
    activa BOOLEAN, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    UNIQUE (codigo)
);

INSERT INTO tenant_servicios_contables.alembic_version (version_num) VALUES ('00f9b652f015') RETURNING tenant_servicios_contables.alembic_version.version_num;

-- Running upgrade 00f9b652f015 -> 90dab873f830

CREATE TABLE tenant_servicios_contables.partidas (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    fecha DATE NOT NULL, 
    descripcion TEXT NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

CREATE TABLE tenant_servicios_contables.detalle_partidas (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    partida_id UUID NOT NULL, 
    cuenta_id UUID NOT NULL, 
    tipo_movimiento VARCHAR(10) NOT NULL, 
    monto NUMERIC(12, 2) NOT NULL, 
    PRIMARY KEY (id)
);

ALTER TABLE tenant_servicios_contables.detalle_partidas ADD CONSTRAINT fk_detalle_partidas_partida FOREIGN KEY(partida_id) REFERENCES tenant_servicios_contables.partidas (id) ON DELETE CASCADE;

ALTER TABLE tenant_servicios_contables.detalle_partidas ADD CONSTRAINT fk_detalle_partidas_cuenta FOREIGN KEY(cuenta_id) REFERENCES tenant_servicios_contables.plan_cuentas (id);

UPDATE tenant_servicios_contables.alembic_version SET version_num='90dab873f830' WHERE tenant_servicios_contables.alembic_version.version_num = '00f9b652f015';

-- Running upgrade 90dab873f830 -> b784c4ae6e9d

CREATE SEQUENCE IF NOT EXISTS tenant_servicios_contables.partidas_numero_seq;

ALTER TABLE tenant_servicios_contables.partidas ADD COLUMN numero INTEGER DEFAULT nextval('tenant_servicios_contables.partidas_numero_seq') NOT NULL;

ALTER TABLE tenant_servicios_contables.partidas ADD COLUMN numero_poliza VARCHAR(50);

ALTER TABLE tenant_servicios_contables.partidas ADD UNIQUE (numero_poliza);

ALTER TABLE tenant_servicios_contables.partidas ADD COLUMN empresa_id UUID NOT NULL;

ALTER TABLE tenant_servicios_contables.partidas ADD CONSTRAINT uq_partidas_numero UNIQUE (numero);

ALTER TABLE tenant_servicios_contables.partidas ADD CONSTRAINT fk_partidas_empresa FOREIGN KEY(empresa_id) REFERENCES tenant_servicios_contables.empresas (id);

UPDATE tenant_servicios_contables.alembic_version SET version_num='b784c4ae6e9d' WHERE tenant_servicios_contables.alembic_version.version_num = '90dab873f830';

-- Running upgrade b784c4ae6e9d -> a989a89a0415

ALTER TABLE tenant_servicios_contables.plan_cuentas ADD COLUMN empresa_id UUID NOT NULL;

ALTER TABLE tenant_servicios_contables.plan_cuentas ADD CONSTRAINT fk_plan_cuentas_empresa FOREIGN KEY(empresa_id) REFERENCES tenant_servicios_contables.empresas (id);

ALTER TABLE tenant_servicios_contables.partidas DROP CONSTRAINT fk_partidas_empresa;

ALTER TABLE tenant_servicios_contables.partidas DROP COLUMN empresa_id;

UPDATE tenant_servicios_contables.alembic_version SET version_num='a989a89a0415' WHERE tenant_servicios_contables.alembic_version.version_num = 'b784c4ae6e9d';

-- Running upgrade a989a89a0415 -> ecac85d2eec2

CREATE TABLE tenant_servicios_contables.secuencias (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    entidad VARCHAR(50) NOT NULL, 
    empresa_id UUID NOT NULL, 
    contador INTEGER DEFAULT '1', 
    PRIMARY KEY (id), 
    CONSTRAINT uq_secuencias_entidad_empresa UNIQUE (entidad, empresa_id)
);

ALTER TABLE tenant_servicios_contables.secuencias ADD CONSTRAINT fk_secuencias_empresa FOREIGN KEY(empresa_id) REFERENCES tenant_servicios_contables.empresas (id);

UPDATE tenant_servicios_contables.alembic_version SET version_num='ecac85d2eec2' WHERE tenant_servicios_contables.alembic_version.version_num = 'a989a89a0415';

-- Running upgrade ecac85d2eec2 -> d90dd406e3ad

CREATE TABLE tenant_servicios_contables.periodos_fiscales (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    nombre VARCHAR(50) NOT NULL, 
    fecha_inicio DATE NOT NULL, 
    fecha_fin DATE NOT NULL, 
    cerrado BOOLEAN DEFAULT false NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id)
);

UPDATE tenant_servicios_contables.alembic_version SET version_num='d90dd406e3ad' WHERE tenant_servicios_contables.alembic_version.version_num = 'ecac85d2eec2';

-- Running upgrade d90dd406e3ad -> a4f888d8ea41

CREATE TABLE tenant_servicios_contables.facturas_electronicas (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    empresa_id UUID NOT NULL, 
    xml_original TEXT NOT NULL, 
    numero_autorizacion VARCHAR(50) NOT NULL, 
    serie VARCHAR(20), 
    numero VARCHAR(20) NOT NULL, 
    fecha_emision TIMESTAMP WITH TIME ZONE NOT NULL, 
    emisor_nit VARCHAR(15) NOT NULL, 
    emisor_nombre VARCHAR(255) NOT NULL, 
    receptor_nit VARCHAR(15) NOT NULL, 
    receptor_nombre VARCHAR(255) NOT NULL, 
    total_gravado NUMERIC(12, 2) DEFAULT '0', 
    total_iva NUMERIC(12, 2) DEFAULT '0', 
    total_exento NUMERIC(12, 2) DEFAULT '0', 
    total NUMERIC(12, 2) NOT NULL, 
    autorizacion_uuid VARCHAR(50), 
    tipo_documento VARCHAR(10), 
    moneda VARCHAR(5), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
    PRIMARY KEY (id), 
    FOREIGN KEY(empresa_id) REFERENCES empresas (id)
);

UPDATE tenant_servicios_contables.alembic_version SET version_num='a4f888d8ea41' WHERE tenant_servicios_contables.alembic_version.version_num = 'd90dd406e3ad';

-- Running upgrade a4f888d8ea41 -> 85e51fb13be5

CREATE TABLE tenant_servicios_contables.factura_detalles (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    factura_id UUID NOT NULL, 
    cantidad NUMERIC(12, 4) NOT NULL, 
    descripcion VARCHAR(500) NOT NULL, 
    precio_unitario NUMERIC(12, 2) NOT NULL, 
    total_linea NUMERIC(12, 2) NOT NULL, 
    iva_linea NUMERIC(12, 2) DEFAULT '0', 
    PRIMARY KEY (id), 
    FOREIGN KEY(factura_id) REFERENCES facturas_electronicas (id) ON DELETE CASCADE
);

UPDATE tenant_servicios_contables.alembic_version SET version_num='85e51fb13be5' WHERE tenant_servicios_contables.alembic_version.version_num = 'a4f888d8ea41';

-- Running upgrade 85e51fb13be5 -> bdac449affae

ALTER TABLE facturas_electronicas ADD COLUMN tipo_cambio NUMERIC(10, 5);

UPDATE tenant_servicios_contables.alembic_version SET version_num='bdac449affae' WHERE tenant_servicios_contables.alembic_version.version_num = '85e51fb13be5';

-- Running upgrade bdac449affae -> ff964c9ca097

ALTER TABLE facturas_electronicas ADD COLUMN tipo_documento_id UUID;

ALTER TABLE facturas_electronicas ADD COLUMN moneda_id UUID;

ALTER TABLE facturas_electronicas ADD CONSTRAINT fk_facturas_tipos_dte FOREIGN KEY(tipo_documento_id) REFERENCES public.tipos_dte (id);

ALTER TABLE facturas_electronicas ADD CONSTRAINT fk_facturas_catalogo_monedas FOREIGN KEY(moneda_id) REFERENCES public.catalogo_monedas (id);

CREATE INDEX ix_facturas_electronicas_tipo_documento_id ON facturas_electronicas (tipo_documento_id);

CREATE INDEX ix_facturas_electronicas_moneda_id ON facturas_electronicas (moneda_id);

UPDATE tenant_servicios_contables.alembic_version SET version_num='ff964c9ca097' WHERE tenant_servicios_contables.alembic_version.version_num = 'bdac449affae';

-- Running upgrade ff964c9ca097 -> e7441e6b3151

ALTER TABLE facturas_electronicas ADD COLUMN fecha_anulacion TIMESTAMP WITH TIME ZONE;

CREATE TABLE facturas_impuestos_especiales (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    factura_id UUID NOT NULL, 
    catalogo_id UUID NOT NULL, 
    monto NUMERIC(12, 2) DEFAULT '0' NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(factura_id) REFERENCES facturas_electronicas (id), 
    FOREIGN KEY(catalogo_id) REFERENCES public.catalogo_impuestos_especiales (id)
);

CREATE INDEX ix_facturas_impuestos_especiales_factura_id ON facturas_impuestos_especiales (factura_id);

CREATE INDEX ix_facturas_impuestos_especiales_catalogo_id ON facturas_impuestos_especiales (catalogo_id);

UPDATE tenant_servicios_contables.alembic_version SET version_num='e7441e6b3151' WHERE tenant_servicios_contables.alembic_version.version_num = 'ff964c9ca097';

COMMIT;

