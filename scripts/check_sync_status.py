import sqlalchemy as sa
e = sa.create_engine("postgresql://eureka:eurekapass@eureka_postgres:5432/eureka_db")
tables = [
    "cache_embargos", "cache_terras_indigenas", "cache_unidades_conservacao",
    "cache_quilombolas", "cache_assentamentos", "cache_prodes",
    "cache_autos_infracao", "cache_florestas_publicas", "cache_alertas_deter",
    "cache_car_ativo",
]
insp = sa.inspect(e)
for t in tables:
    if insp.has_table(t):
        n = e.execute(sa.text(f"SELECT COUNT(*) FROM {t}")).scalar()
        print(f"  {t}: {n} registros")
    else:
        print(f"  {t}: NAO EXISTE")
