DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.columns
        WHERE table_name LIKE 'cache_%'
          AND table_name != 'cache_sync_log'
          AND column_name = 'geom'
        GROUP BY table_name
    LOOP
        EXECUTE 'UPDATE ' || t || ' SET geom = ST_FlipCoordinates(geom)';
        RAISE NOTICE 'Corrigido: %', t;
    END LOOP;
END $$;
