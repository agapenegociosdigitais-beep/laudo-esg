"""
Endpoints para gera��o e download de relat�rios PDF.
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.deps import SessaoDB, UsuarioAtual
from app.core.config import get_settings
from app.models.analise import Analise
from app.models.propriedade import Propriedade
from app.models.relatorio import Relatorio
from app.schemas.relatorio import RelatorioRequest, RelatorioResposta
from app.services.relatorio_service import RelatorioService

router = APIRouter()
relatorio_service = RelatorioService()
settings = get_settings()


@router.post("/gerar", response_model=RelatorioResposta, status_code=status.HTTP_201_CREATED)
async def gerar_relatorio(dados: RelatorioRequest, db: SessaoDB, usuario: UsuarioAtual):
    """
    Gera um relat�rio PDF para uma an�lise conclu�da.
    O PDF � salvo no servidor e um link de download � retornado.
    """
    # Verifica se a an�lise existe e est� conclu�da
    resultado_analise = await db.execute(
        select(Analise).where(Analise.id == dados.analise_id)
    )
    analise = resultado_analise.scalar_one_or_none()

    if not analise:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="An�lise n�o encontrada.",
        )

    if analise.status != "concluido":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A an�lise ainda n�o foi conclu�da. Status atual: {analise.status}",
        )

    # Busca a propriedade
    resultado_prop = await db.execute(
        select(Propriedade).where(Propriedade.id == analise.propriedade_id)
    )
    propriedade = resultado_prop.scalar_one_or_none()

    if not propriedade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Propriedade da an�lise n�o encontrada.",
        )

    # Gera o PDF
    try:
        caminho_pdf, nome_arquivo = await relatorio_service.gerar_pdf(
            analise=analise,
            propriedade=propriedade,
            usuario=usuario,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar relat�rio: {str(e)}",
        )

    # Registra no banco
    relatorio = Relatorio(
        usuario_id=usuario.id,
        propriedade_id=propriedade.id,
        analise_id=analise.id,
        nome_arquivo=nome_arquivo,
        caminho_arquivo=str(caminho_pdf),
        tamanho_bytes=Path(caminho_pdf).stat().st_size if Path(caminho_pdf).exists() else None,
        status="concluido",
    )
    db.add(relatorio)
    await db.flush()
    await db.refresh(relatorio)

    return RelatorioResposta(
        id=relatorio.id,
        nome_arquivo=relatorio.nome_arquivo,
        status=relatorio.status,
        tamanho_bytes=relatorio.tamanho_bytes,
        criado_em=relatorio.criado_em,
        url_download=f"/api/v1/relatorios/{relatorio.id}/download",
    )


@router.get("/{relatorio_id}/download")
async def download_relatorio(relatorio_id: uuid.UUID, db: SessaoDB, usuario: UsuarioAtual):
    """Faz o download do PDF do relat�rio gerado."""
    resultado = await db.execute(
        select(Relatorio).where(
            Relatorio.id == relatorio_id,
            Relatorio.usuario_id == usuario.id,
        )
    )
    relatorio = resultado.scalar_one_or_none()

    if not relatorio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Relat�rio n�o encontrado ou sem permiss�o de acesso.",
        )

    caminho = Path(relatorio.caminho_arquivo)
    if not caminho.exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Arquivo do relat�rio n�o encontrado no servidor.",
        )

    return FileResponse(
        path=str(caminho),
        media_type="application/pdf",
        filename=relatorio.nome_arquivo,
    )
