DROP TABLE IF EXISTS public.empresas CASCADE;
DROP TABLE IF EXISTS public.plan_cuentas CASCADE;
DROP TABLE IF EXISTS public.partidas CASCADE;
DROP TABLE IF EXISTS public.detalle_partidas CASCADE;
DROP TABLE IF EXISTS public.secuencias CASCADE;
DROP TABLE IF EXISTS public.periodos_fiscales CASCADE;
DROP TABLE IF EXISTS public.facturas_electronicas CASCADE;
DROP TABLE IF EXISTS public.factura_detalles CASCADE
-- Si existe alguna tabla de historial huérfana:
DROP TABLE IF EXISTS public.alembic_version_tenant CASCADE;

