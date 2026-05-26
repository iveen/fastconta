-- Transfiere ownership de todos los schemas de tenant a fastconta_user
DO $$
DECLARE s TEXT; t TEXT;
BEGIN
  FOR s IN SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE 'tenant_%' LOOP
    FOR t IN SELECT table_name FROM information_schema.tables WHERE table_schema = s AND table_type = 'BASE TABLE' LOOP
      EXECUTE format('ALTER TABLE %I.%I OWNER TO fastconta_user', s, t);
    END LOOP;
    FOR t IN SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = s LOOP
      EXECUTE format('ALTER SEQUENCE %I.%I OWNER TO fastconta_user', s, t);
    END LOOP;
    EXECUTE format('ALTER SCHEMA %I OWNER TO fastconta_user', s);
  END LOOP;
END $$;