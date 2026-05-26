-- 🔹 Script para aplicar estructura normalizada en todos los tenants
-- ✅ Seguro ejecutar múltiples veces (no duplica columnas ni constraints)
DO $$
DECLARE
    schema_rec RECORD;
    col_exists BOOLEAN;
    fk_exists BOOLEAN;
BEGIN
    FOR schema_rec IN
        SELECT schema_name FROM information_schema.schemata
        WHERE schema_name LIKE 'tenant_%' ORDER BY schema_name
    LOOP
        RAISE NOTICE '🔹 Procesando schema: %', schema_rec.schema_name;

        -- 1️⃣ Agregar columnas (ADD COLUMN IF NOT EXISTS es nativo en PG 9.6+)
        EXECUTE format('ALTER TABLE %I.facturas_electronicas ADD COLUMN IF NOT EXISTS tipo_documento_id UUID', schema_rec.schema_name);
        EXECUTE format('ALTER TABLE %I.facturas_electronicas ADD COLUMN IF NOT EXISTS moneda_id UUID', schema_rec.schema_name);
        EXECUTE format('ALTER TABLE %I.facturas_electronicas ADD COLUMN IF NOT EXISTS tipo_cambio NUMERIC(10,5)', schema_rec.schema_name);

        -- 2️⃣ Foreign Key: tipo_documento_id -> public.tipos_dte
        SELECT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_schema = schema_rec.schema_name
              AND table_name = 'facturas_electronicas'
              AND constraint_name = 'fk_facturas_tipos_dte'
              AND constraint_type = 'FOREIGN KEY'
        ) INTO fk_exists;

        IF NOT fk_exists THEN
            EXECUTE format(
                'ALTER TABLE %I.facturas_electronicas ADD CONSTRAINT fk_facturas_tipos_dte '
                'FOREIGN KEY (tipo_documento_id) REFERENCES public.tipos_dte(id) ON DELETE SET NULL',
                schema_rec.schema_name
            );
            RAISE NOTICE '   ✅ FK fk_facturas_tipos_dte creada';
        ELSE
            RAISE NOTICE '   ℹ️  FK fk_facturas_tipos_dte ya existe';
        END IF;

        -- 3️⃣ Foreign Key: moneda_id -> public.catalogo_monedas
        SELECT EXISTS (
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_schema = schema_rec.schema_name
              AND table_name = 'facturas_electronicas'
              AND constraint_name = 'fk_facturas_catalogo_monedas'
              AND constraint_type = 'FOREIGN KEY'
        ) INTO fk_exists;

        IF NOT fk_exists THEN
            EXECUTE format(
                'ALTER TABLE %I.facturas_electronicas ADD CONSTRAINT fk_facturas_catalogo_monedas '
                'FOREIGN KEY (moneda_id) REFERENCES public.catalogo_monedas(id) ON DELETE SET NULL',
                schema_rec.schema_name
            );
            RAISE NOTICE '   ✅ FK fk_facturas_catalogo_monedas creada';
        ELSE
            RAISE NOTICE '   ℹ️  FK fk_facturas_catalogo_monedas ya existe';
        END IF;

    END LOOP;
    RAISE NOTICE '🎉 Finalizado. Todos los tenants actualizados.';
END $$;


