"""
Endpoints de autentica��o: registro, login e dados do usu�rio atual.
"""
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessaoDB, UsuarioAtual
from app.core.security import criar_token_acesso, gerar_hash_senha, verificar_senha
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, RegistroResposta, TokenResposta, UsuarioCriar, UsuarioResposta

router = APIRouter()


@router.post("/registrar", response_model=RegistroResposta, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(dados: UsuarioCriar, db: SessaoDB):
    """
    Cria uma nova conta na plataforma Eureka Terra.
    Retorna o token JWT para acesso imediato ap�s o registro.
    """
    # Verifica se o e-mail j� est� em uso
    resultado = await db.execute(select(Usuario).where(Usuario.email == dados.email))
    if resultado.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este e-mail j� est� cadastrado. Use outro e-mail ou fa�a login.",
        )

    # Cria o novo usu�rio
    usuario = Usuario(
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        nome=dados.nome,
        empresa=dados.empresa,
        perfil=dados.perfil,
        ativo=False,  # Aguarda aprovação do admin
    )
    db.add(usuario)
    await db.flush()  # Gera o ID sem commit final
    await db.refresh(usuario)

    return RegistroResposta(
        usuario=UsuarioResposta.model_validate(usuario),
        mensagem="Conta criada com sucesso. Aguardando aprovação do administrador.",
        requer_aprovacao=True,
    )


@router.post("/login", response_model=TokenResposta)
async def login(dados: LoginRequest, db: SessaoDB):
    """
    Autentica o usu�rio e retorna o token JWT de acesso.
    """
    resultado = await db.execute(select(Usuario).where(Usuario.email == dados.email))
    usuario = resultado.scalar_one_or_none()

    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Entre em contato com o suporte.",
        )

    token = criar_token_acesso(str(usuario.id))
    return TokenResposta(
        access_token=token,
        usuario=UsuarioResposta.model_validate(usuario),
    )


@router.get("/me", response_model=UsuarioResposta)
async def obter_perfil(usuario: UsuarioAtual):
    """Retorna os dados do usu�rio autenticado."""
    return UsuarioResposta.model_validate(usuario)
