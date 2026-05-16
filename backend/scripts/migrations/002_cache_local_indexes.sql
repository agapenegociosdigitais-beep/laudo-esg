-- Indices espaciais GiST para cache local (GeoServer nacional unificado)

CREATE INDEX IF NOT EXISTS idx_cache_prodes_geom ON cache_prodes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cache_embargos_geom ON cache_embargos USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cache_terras_indigenas_geom ON cache_terras_indigenas USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cache_unidades_conservacao_geom ON cache_unidades_conservacao USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cache_quilombolas_geom ON cache_quilombolas USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cache_assentamentos_geom ON cache_assentamentos USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cache_autos_infracao_geom ON cache_autos_infracao USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cache_florestas_publicas_geom ON cache_florestas_publicas USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cache_alertas_deter_geom ON cache_alertas_deter USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cache_car_ativo_geom ON cache_car_ativo USING GIST (geom);
