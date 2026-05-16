"""Modelos das tabelas de cache local — GeoServer nacional unificado."""

from geoalchemy2 import Geometry
from sqlalchemy import Column, Float, Integer, String, DateTime, Text, func
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class CacheProdes(Base):
    __tablename__ = "cache_prodes"
    __table_args__ = {"comment": "Desmatamento PRODES (GeoServer nacional)"}

    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False, index=True)
    area_km = Column(Float, nullable=True)
    state = Column(String(2), nullable=True, index=True)
    main_class = Column(String(50), nullable=True)
    class_name = Column(String(50), nullable=True)
    image_date = Column(String(20), nullable=True)
    path_row = Column(String(20), nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False, index=True)


class CacheEmbargos(Base):
    __tablename__ = "cache_embargos"
    __table_args__ = {"comment": "Embargos (IBAMA+SEMAS+ICMBIO) — GeoServer nacional"}

    id = Column(Integer, primary_key=True)
    num_tad = Column(String(100), nullable=True, index=True)
    seq_tad = Column(String(100), nullable=True)
    orgao = Column(String(50), nullable=True, index=True)
    data_embargo = Column(String(30), nullable=True)
    area_ha = Column(Float, nullable=True)
    nome_infrator = Column(String(255), nullable=True)
    cpf_cnpj = Column(String(50), nullable=True)
    descricao = Column(Text, nullable=True)
    situacao = Column(String(50), nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False, index=True)


class CacheTI(Base):
    __tablename__ = "cache_terras_indigenas"
    __table_args__ = {"comment": "Terras Indigenas (FUNAI) — GeoServer nacional"}

    id = Column(Integer, primary_key=True)
    nome_ti = Column(String(255), nullable=True, index=True)
    etnia = Column(String(255), nullable=True)
    fase = Column(String(100), nullable=True)
    modalidade = Column(String(100), nullable=True)
    municipio = Column(String(255), nullable=True)
    orgao = Column(String(50), nullable=True)
    area_ha = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False, index=True)


class CacheUC(Base):
    __tablename__ = "cache_unidades_conservacao"
    __table_args__ = {"comment": "Unidades de Conservacao (MMA/ICMBIO/IDEFLOR) — GeoServer nacional"}

    id = Column(Integer, primary_key=True)
    nome_uc = Column(String(255), nullable=True, index=True)
    categoria = Column(String(100), nullable=True)
    tipo = Column(String(50), nullable=True)
    cod_cnuc = Column(String(50), nullable=True)
    ano_criacao = Column(String(30), nullable=True)
    orgao = Column(String(50), nullable=True)
    area_ha = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False, index=True)


class CacheQuilombola(Base):
    __tablename__ = "cache_quilombolas"
    __table_args__ = {"comment": "Areas Quilombolas (ITERPA+INCRA) — GeoServer nacional"}

    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=True, index=True)
    orgao = Column(String(50), nullable=True)
    processo = Column(String(50), nullable=True)
    area_ha = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False, index=True)


class CacheAssentamento(Base):
    __tablename__ = "cache_assentamentos"
    __table_args__ = {"comment": "Assentamentos (INCRA+ITERPA) — GeoServer nacional"}

    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=True, index=True)
    orgao = Column(String(50), nullable=True)
    codigo = Column(String(50), nullable=True)
    familias = Column(Integer, nullable=True)
    modalidade = Column(String(50), nullable=True)
    area_ha = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False, index=True)


class CacheAutoInfracao(Base):
    __tablename__ = "cache_autos_infracao"
    __table_args__ = {"comment": "Autos de Infracao (IBAMA+SEMAS) — GeoServer nacional"}

    id = Column(Integer, primary_key=True)
    num_auto = Column(String(100), nullable=True, index=True)
    data_lavratura = Column(String(30), nullable=True)
    tipo_infracao = Column(String(100), nullable=True)
    nome_infrator = Column(String(255), nullable=True)
    cpf_cnpj = Column(String(50), nullable=True)
    orgao = Column(String(50), nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False, index=True)


class CacheFlorestaPublica(Base):
    __tablename__ = "cache_florestas_publicas"
    __table_args__ = {"comment": "Florestas Publicas (SFB) — GeoServer nacional"}

    id = Column(Integer, primary_key=True)
    nome = Column(String(255), nullable=True, index=True)
    classe = Column(String(50), nullable=True)
    categoria = Column(String(100), nullable=True)
    orgao = Column(String(50), nullable=True)
    area_ha = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False, index=True)


class CacheDeter(Base):
    __tablename__ = "cache_alertas_deter"
    __table_args__ = {"comment": "Alertas DETER (INPE) — GeoServer nacional"}

    id = Column(Integer, primary_key=True)
    classe_alerta = Column(String(100), nullable=True, index=True)
    data_alerta = Column(String(30), nullable=True)
    ano = Column(Integer, nullable=True, index=True)
    uf = Column(String(2), nullable=True)
    area_ha = Column(Float, nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False, index=True)


class CacheCarAtivo(Base):
    __tablename__ = "cache_car_ativo"
    __table_args__ = {"comment": "CARs Ativos (PA) — GeoServer nacional"}

    id = Column(Integer, primary_key=True)
    cod_imovel = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(String(50), nullable=True, index=True)
    nome_imovel = Column(String(255), nullable=True)
    nome_proprietario = Column(String(255), nullable=True)
    cpf_cnpj = Column(String(50), nullable=True)
    municipio = Column(String(255), nullable=True)
    area_ha = Column(Float, nullable=True)
    condicao = Column(String(500), nullable=True)
    tipo_imovel = Column(String(50), nullable=True)
    geom = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True, index=True)
    sincronizado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CacheSyncLog(Base):
    __tablename__ = "cache_sync_log"
    __table_args__ = {"comment": "Registro de sincronizacoes"}

    id = Column(Integer, primary_key=True)
    tabela = Column(String(100), nullable=False, index=True)
    registros_importados = Column(Integer, nullable=False, default=0)
    erros = Column(Integer, nullable=False, default=0)
    duracao_segundos = Column(Float, nullable=True)
    detalhes = Column(JSONB, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
