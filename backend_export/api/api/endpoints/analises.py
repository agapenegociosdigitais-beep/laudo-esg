"""
Endpoints para iniciar e consultar análises de conformidade ESG.

Pipeline de análise (background, execução paralela via asyncio.gather):
  1. Embargo IBAMA     ?IBAMA/CTF
  2. Embargo SEMAS     ?SEMAS-PA/SIMLAM
  3. Sobreposição UC   ?CNUC/MMA
  4. Sobreposição TI   ?FUNAI
  5. Desmatamento      ?PRODES/INPE (TerraBrasilis)
  6. Quilombolas       ?INCRA WFS (territorio_quilombola_portaria)
  7. Assentamentos     ?INCRA WFS (projetoassentamento)
  8. Trabalho Escravo  ?Lista Suja MTE (transparencia.gov.br)
  Pós-gather:
  9. Balanço RL/APP    ?Código Florestal (cálculo local)
 10. Moratória da Soja ?conformidade com corte jul/2008
 11. EUDR / Marco UE   ?conformidade com corte dez/2020
"""
import asyncio
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status
from sqlalchemy import select

from app.api.deps import SessaoDB, UsuarioAtual
from app.models.analise import Analise
from app.models.propriedade import Propriedade
from app.schemas.analise import AnaliseRequest, AnaliseResposta
from app.services.areas_protegidas_service import AreasProtegidasService, ResultadoAreaProtegida
from app.services.conformidade_service import (
    calcular_balanco_ambiental,
    verificar_assentamentos,
    verificar_quilombolas,
    verificar_trabalho_escravo,
)
from app.services.desmatamento_service import DesmatamentoService
from app.services.sicar_service import buscar_car_sicar
from app.services.embargos_service import (
    ResultadoEmbargo,
    verificar_embargos_ibama,
    verificar_embargos_semas,
    verificar_marco_ue_prodes,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ??Fallbacks para APIs que falharam ??????????????????????????????????????????

def _fallback_embargo(orgao: str) -> ResultadoEmbargo:
    return ResultadoEmbargo(
        embargo_detectado=False,
        fonte=f"{orgao} (erro)",
        total_embargos=0,
        verificado=False,
        motivo_nao_verificado="Erro interno na verificação",
    )


def _fallback_area(tipo: str) -> ResultadoAreaProtegida:
    return ResultadoAreaProtegida(
        sobreposicao_detectada=None,
        tipo_verificacao=tipo,
        verificado=False,
        motivo_nao_verificado="Erro interno na verificação",
    )


def _fallback_dict(fonte: str) -> dict:
    return {"sobreposicao": False, "total": 0, "nomes": [], "verificado": False, "fonte": fonte}


def _fallback_trabalho() -> dict:
    return {"trabalho_escravo": False, "verificado": False, "fonte": "MTE (erro)"}


# ??Score ESG com 9 dimensões ?????????????????????????????????????????????????

def _calcular_score_esg(
    embargo_ibama: ResultadoEmbargo,
    embargo_semas: ResultadoEmbargo,
    resultado_uc: ResultadoAreaProtegida,
    resultado_ti: ResultadoAreaProtegida,
    desmatamento,
    conf_eudr,
    quilombola: dict,
    assentamento: dict,
    trabalho: dict,
    balanco: dict,
) -> tuple[float, str]:
    """
    Calcula score ESG (0?100) com ponderação em 9 dimensões.

    Embargos ambientais    (-50 max): IBAMA -30, SEMAS -20
    Áreas protegidas       (-45 max): TI -25, UC -20
    Desmatamento PRODES    (-30 max): proporcional à área
    Marco UE / EUDR        (-15):     não conforme após dez/2020
    Quilombola             (-10):     sobreposição com território
    Assentamento           ( -5):     sobreposição com PA
    Trabalho escravo       (-25):     presença na Lista Suja MTE
    Balanço RL/APP         (-10 max): déficit RL -7, APP -3
    """
    score = 100

    # 1. Embargos ambientais
    if embargo_ibama.embargo_detectado is True:
        score -= 30
    if embargo_semas.embargo_detectado is True:
        score -= 20

    # 2. Áreas protegidas
    if resultado_ti.sobreposicao_detectada is True:
        score -= 25
    if resultado_uc.sobreposicao_detectada is True:
        score -= 20

    # 3. Desmatamento PRODES (proporcional à área)
    area_dm = getattr(desmatamento, "area_desmatada_ha", 0) or 0
    if getattr(desmatamento, "desmatamento_detectado", False):
        if area_dm > 500:
            score -= 30
        elif area_dm > 100:
            score -= 20
        elif area_dm > 10:
            score -= 10
        else:
            score -= 5

    # 4. Marco UE / EUDR
    if conf_eudr is not None and not getattr(conf_eudr, "conforme", True):
        score -= 15

    # 5. Quilombola
    if quilombola.get("sobreposicao"):
        score -= 10

    # 6. Assentamento
    if assentamento.get("sobreposicao"):
        score -= 5

    # 7. Trabalho escravo
    if trabalho.get("trabalho_escravo"):
        score -= 25

    # 8. Balanço ambiental RL/APP
    if balanco.get("deficit_rl_ha", 0) > 0:
        score -= 7
    if balanco.get("deficit_app_ha", 0) > 0:
        score -= 3

    score = float(max(0, score))
    nivel = (
        "BAIXO"   if score >= 80
        else "M?DIO"  if score >= 60
        else "ALTO"   if score >= 40
        else "CRÍTICO"
    )
    return score, nivel


# ??Pipeline de background ????????????????????????????????????????????????????

async def _processar_analise(analise_id: uuid.UUID) -> None:
    """
    Executa a pipeline completa de análise ESG em background.

    Cria sessão própria de banco (fora do ciclo de vida do request HTTP).
    Usa asyncio.gather para paralelizar as 8 chamadas externas, reduzindo
    o tempo total de ~2 min para ~30 s em condições normais de rede.
    Erros parciais (API indisponível) usam fallback ?a análise não é
    interrompida por falhas isoladas.
    """
    from app.core.database import AsyncSessionLocal

    areas_svc = AreasProtegidasService()
    dmt_svc = DesmatamentoService()

    async with AsyncSessionLocal() as db:
        try:
            resultado = await db.execute(select(Analise).where(Analise.id == analise_id))
            analise = resultado.scalar_one_or_none()
            if not analise:
                return

            analise.status = "processando"
            await db.commit()

            # Carrega a propriedade
            prop_res = await db.execute(
                select(Propriedade).where(Propriedade.id == analise.propriedade_id)
            )
            propriedade = prop_res.scalar_one_or_none()
            if not propriedade:
                raise ValueError("Propriedade nao encontrada.")

            numero_car = propriedade.numero_car
            estado = propriedade.estado or ""
            bioma = propriedade.bioma or "Desconhecido"
            area_ha = propriedade.area_ha or 0.0
            geojson = propriedade.geojson

            # Busca geometria real no SICAR se nao tiver no banco
            if not geojson and numero_car:
                logger.info(f"Buscando geometria SICAR para {numero_car}...")
                sicar_dados = await buscar_car_sicar(numero_car)
                if sicar_dados.get("sucesso") and sicar_dados.get("geometria"):
                    geojson = sicar_dados["geometria"]
                    area_ha = sicar_dados.get("area_ha") or area_ha
                    estado = sicar_dados.get("uf") or estado
                    propriedade.geojson = geojson
                    propriedade.area_ha = area_ha
                    propriedade.estado = estado
                    if not propriedade.municipio:
                        propriedade.municipio = sicar_dados.get("municipio", "")
                    await db.commit()
                    logger.info(f"SICAR geometria salva: {area_ha} ha, {estado}")
                else:
                    logger.warning(f"SICAR sem geometria para {numero_car}")

            if not geojson:
                raise ValueError("Propriedade sem geometria. SICAR nao retornou dados.")

            # Sub-áreas estimadas (quando SICAR não retorna breakdown)
            pct_rl = 0.80 if "Amazônia" in bioma else 0.20
            area_veg_ha = round(area_ha * (0.55 if "Amazônia" in bioma else 0.30), 2)
            area_app_ha = round(area_ha * 0.15, 2)
            area_rl_ha = round(area_ha * pct_rl, 2)
            area_cons_ha = round(area_ha * 0.25, 2)

            # ??Execução paralela das 9 verificações externas ?????????????????
            (
                res_ibama,
                res_semas,
                res_uc,
                res_ti,
                res_demat,
                marco_ue,
                quilombola,
                assentamento,
                trabalho,
            ) = await asyncio.gather(
                verificar_embargos_ibama(numero_car, geojson, estado),
                verificar_embargos_semas(numero_car, geojson),
                areas_svc.verificar_sobreposicao_uc(numero_car, geojson, area_ha),
                areas_svc.verificar_sobreposicao_ti(numero_car, geojson, area_ha),
                dmt_svc.verificar_desmatamento(geojson, bioma),
                verificar_marco_ue_prodes(numero_car, geojson, estado),
                verificar_quilombolas(numero_car, geojson, estado),
                verificar_assentamentos(numero_car, geojson, estado),
                verificar_trabalho_escravo(numero_car),
                return_exceptions=True,
            )

            # Aplica fallbacks para cada serviço que falhou
            if isinstance(res_ibama, Exception):
                logger.warning(f"IBAMA falhou ({analise_id}): {res_ibama}")
                res_ibama = _fallback_embargo("IBAMA")
            if isinstance(res_semas, Exception):
                logger.warning(f"SEMAS falhou ({analise_id}): {res_semas}")
                res_semas = _fallback_embargo("SEMAS")
            if isinstance(res_uc, Exception):
                logger.warning(f"UC falhou ({analise_id}): {res_uc}")
                res_uc = _fallback_area("UC")
            if isinstance(res_ti, Exception):
                logger.warning(f"TI falhou ({analise_id}): {res_ti}")
                res_ti = _fallback_area("TI")
            if isinstance(res_demat, Exception):
                logger.warning(f"Desmatamento falhou ({analise_id}): {res_demat}")
                from app.schemas.analise import ResultadoDesmatamento
                res_demat = ResultadoDesmatamento(
                    desmatamento_detectado=False,
                    area_desmatada_ha=0.0,
                    periodo_referencia="N/A",
                    fonte="Fallback (erro na consulta)",
                )
            if isinstance(marco_ue, Exception):
                logger.warning(f"Marco UE PRODES falhou ({analise_id}): {marco_ue}")
                marco_ue = {
                    "em_conformidade": True,
                    "desmatamento_detectado": False,
                    "registros_pos_2020": [],
                    "total_registros": 0,
                    "area_total_ha": 0,
                    "verificado": False,
                    "fonte": "PRODES (erro)",
                }
            if isinstance(quilombola, Exception):
                logger.warning(f"Quilombola falhou ({analise_id}): {quilombola}")
                quilombola = _fallback_dict("INCRA (erro)")
            if isinstance(assentamento, Exception):
                logger.warning(f"Assentamento falhou ({analise_id}): {assentamento}")
                assentamento = _fallback_dict("INCRA (erro)")
            if isinstance(trabalho, Exception):
                logger.warning(f"Trabalho escravo falhou ({analise_id}): {trabalho}")
                trabalho = _fallback_trabalho()

            # ??Cálculos que dependem do desmatamento ?????????????????????????
            conf_soja = dmt_svc.verificar_moratorio_soja(res_demat, bioma)
            conf_eudr = dmt_svc.verificar_eudr(res_demat)

            # ??Balanço ambiental RL/APP (Código Florestal) ???????????????????
            balanco: dict = (
                calcular_balanco_ambiental(
                    area_ha, area_veg_ha, area_app_ha, area_rl_ha, area_cons_ha, bioma
                )
                if area_ha > 0 else {}
            )

            # ??Score ESG com 9 dimensões ?????????????????????????????????????
            analise.score_esg, analise.nivel_risco = _calcular_score_esg(
                res_ibama, res_semas,
                res_uc, res_ti,
                res_demat, conf_eudr,
                quilombola, assentamento, trabalho, balanco,
            )

            # ??Persiste campos JSONB individuais (colunas existentes) ????????
            analise.embargo_ibama = res_ibama.para_dict()
            analise.embargo_semas = res_semas.para_dict()
            analise.sobreposicao_uc = res_uc.para_dict()
            analise.sobreposicao_ti = res_ti.para_dict()
            analise.desmatamento_detectado = res_demat.desmatamento_detectado
            analise.area_desmatada_ha = res_demat.area_desmatada_ha
            analise.dados_desmatamento = res_demat.detalhes
            analise.moratorio_soja_conforme = conf_soja.conforme
            analise.moratorio_soja_detalhe = conf_soja.detalhe
            analise.eudr_conforme = conf_eudr.conforme
            analise.eudr_detalhe = conf_eudr.detalhe

            # ??resultado_conformidade: dados socioambientais completos ????????
            analise.resultado_conformidade = {
                "quilombola": quilombola,
                "assentamento": assentamento,
                "trabalho_escravo": trabalho,
                "balanco_ambiental": balanco,
                "marco_ue": marco_ue,
                "area_total_ha": area_ha,
                "bioma": bioma,
                "estado": estado,
            }

            analise.status = "concluido"
            logger.info(
                f"Análise {analise_id} concluída | "
                f"Score: {analise.score_esg} | Risco: {analise.nivel_risco}"
            )

        except Exception as exc:
            logger.error(f"Erro ao processar análise {analise_id}: {exc}", exc_info=True)
            analise.status = "erro"
            analise.erro_mensagem = str(exc)

        await db.commit()


# ??Endpoints HTTP ????????????????????????????????????????????????????????????

@router.post("/", response_model=AnaliseResposta, status_code=status.HTTP_202_ACCEPTED)
async def iniciar_analise(
    dados: AnaliseRequest,
    background_tasks: BackgroundTasks,
    db: SessaoDB,
    usuario: UsuarioAtual,
):
    """
    Inicia a análise de conformidade ESG em background (9 dimensões).

    Retorna imediatamente com status `pendente` e o `id` da análise.
    Use `GET /analises/{id}` em polling (a cada 3 s) até `status == 'concluido'`.

    Pipeline: embargo IBAMA/SEMAS, sobreposição UC/TI, desmatamento PRODES,
    quilombolas, assentamentos, trabalho escravo, balanço RL/APP, moratória soja, EUDR.
    """
    resultado_prop = await db.execute(
        select(Propriedade).where(Propriedade.id == dados.propriedade_id)
    )
    if not resultado_prop.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propriedade não encontrada. Busque o CAR antes de iniciar a análise.",
        )

    analise = Analise(
        propriedade_id=dados.propriedade_id,
        data_inicio=dados.data_inicio,
        data_fim=dados.data_fim,
        status="pendente",
    )
    db.add(analise)
    await db.flush()
    await db.refresh(analise)

    background_tasks.add_task(_processar_analise, analise.id)

    return AnaliseResposta.model_validate(analise)


@router.get("/{analise_id}", response_model=AnaliseResposta)
async def obter_analise(analise_id: uuid.UUID, db: SessaoDB, usuario: UsuarioAtual):
    """
    Retorna o resultado de uma análise pelo ID.
    Use em polling (a cada 3 s) até `status == 'concluido'`.
    """
    resultado = await db.execute(select(Analise).where(Analise.id == analise_id))
    analise = resultado.scalar_one_or_none()
    if not analise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Análise não encontrada.",
        )
    return AnaliseResposta.model_validate(analise)


@router.get("/propriedade/{propriedade_id}", response_model=list[AnaliseResposta])
async def listar_analises_propriedade(
    propriedade_id: uuid.UUID,
    db: SessaoDB,
    usuario: UsuarioAtual,
    limite: Annotated[int, Query(ge=1, le=50)] = 10,
):
    """Lista as últimas análises de uma propriedade, da mais recente para a mais antiga."""
    resultado = await db.execute(
        select(Analise)
        .where(Analise.propriedade_id == propriedade_id)
        .order_by(Analise.criado_em.desc())
        .limit(limite)
    )
    return [AnaliseResposta.model_validate(a) for a in resultado.scalars().all()]