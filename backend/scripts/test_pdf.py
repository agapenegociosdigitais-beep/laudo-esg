import asyncio, os, sys
sys.path.insert(0, ".")
from app.services.relatorio_service import RelatorioService
from app.core.database import AsyncSessionLocal
from app.models.analise import Analise
from app.models.propriedade import Propriedade
from app.models.usuario import Usuario
from sqlalchemy import select

async def test():
    async with AsyncSessionLocal() as db:
        prop = (await db.execute(select(Propriedade).where(
            Propriedade.numero_car == "PA-1506005-AD0C4CCB1A764A3092B1FC8C71A0873A"
        ))).scalar_one_or_none()
        analise = (await db.execute(select(Analise).where(
            Analise.propriedade_id == prop.id
        ).order_by(Analise.criado_em.desc()).limit(1))).scalar_one_or_none()
        user = (await db.execute(select(Usuario).where(
            Usuario.email == "admin@eurekaterra.com"
        ))).scalar_one_or_none()
        svc = RelatorioService()
        path, name = await svc.gerar_pdf(analise, prop, user)
        print(f"PDF OK: {os.path.getsize(path) / 1024:.0f} KB")

asyncio.run(test())
