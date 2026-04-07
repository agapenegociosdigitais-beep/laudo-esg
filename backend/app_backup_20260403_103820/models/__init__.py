"""Models do banco de dados Eureka Terra."""
from app.models.usuario import Usuario
from app.models.propriedade import Propriedade
from app.models.analise import Analise
from app.models.relatorio import Relatorio

__all__ = ["Usuario", "Propriedade", "Analise", "Relatorio"]
