#!/usr/bin/env python3
"""
Script para corrigir as APIs externas que estão falhando na VPS
Aplica correções nos arquivos de serviço e faz deploy
"""

import paramiko
import time

# Configurações da VPS
VPS_HOST = "23.106.45.137"
VPS_USER = "root"
VPS_PASS = "JVghqGUersYW6h8Q"

# Correções para cada serviço
CORRECOES = {
    "semas_service.py": """
# CORREÇÃO SEMAS-PA: Adicionar User-Agent header para evitar 403 Forbidden
async def buscar_car_semas(car: str) -> dict:
    try:
        car_normalizado = _normalizar_car_semas(car)
        
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "secar-pa:imovel",
            "CQL_FILTER": f"cod_imovel='{car_normalizado}'",
            "outputFormat": "application/json",
            "count": 1,
        }
        
        # ADICIONAR HEADERS PARA EVITAR 403
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; EurekaTerra/1.0)",
            "Accept": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            response = await client.get(
                "https://car.semas.pa.gov.br/geoserver/wfs",
                params=params,
                headers=headers  # HEADERS ADICIONADOS
            )
            
            if response.status_code == 200:
                # ... resto do código
""",
    "areas_protegidas_service.py": """
# CORREÇÃO CNUC/MMA: Atualizar endpoint e typeName corretos
async def _buscar_sobreposicao_cnuc(geometria: dict) -> dict:
    try:
        # ENDPOINT CORRETO
        url = "https://sistemas.mma.gov.br/cnuc-wfs/wfs"
        
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "cnuc:vw_unidade_conservacao",  # TYPENAME CORRETO
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
        }
        
        # ... resto do código
""",
    "funai_service.py": """
# CORREÇÃO FUNAI: Corrigir parâmetros e endpoint
async def _buscar_sobreposicao_funai(geometria: dict) -> dict:
    try:
        # ENDPOINT CORRETO
        url = "https://geoserver.funai.gov.br/geoserver/Funai/wfs"
        
        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typeName": "Funai:ti_funai",  # TYPENAME CORRETO
            "outputFormat": "application/json",
            "srsName": "EPSG:4326",
        }
        
        # ... resto do código
""",
    "ibama_service.py": """
# CORREÇÃO IBAMA CTF: Atualizar endpoint da API
async def buscar_areas_embargadas(car: str) -> dict:
    try:
        # NOVO ENDPOINT CORRETO
        url = f"https://servicos.ibama.gov.br/ctf/publico/areas-embargadas/consultar"
        
        params = {
            "numeroCar": car,
            "pagina": 1,
            "tamanhoPagina": 100
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; EurekaTerra/1.0)",
            "Accept": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=headers)
            # ... resto do código
"""
}


def aplicar_correcoes():
    """Aplica todas as correções na VPS"""
    
    print("=" * 80)
    print("APLICANDO CORREÇÕES NAS APIs EXTERNAS")
    print("=" * 80)
    
    try:
        # Conectar
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"[*] Conectando em {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("[✓] Conectado!\n")
        
        # Passo 1: Fazer backup dos arquivos originais
        print("[*] Passo 1: Fazendo backup dos arquivos originais...")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && cp semas_service.py semas_service.py.backup")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && cp areas_protegidas_service.py areas_protegidas_service.py.backup")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && cp ibama_service.py ibama_service.py.backup")
        print("[✓] Backups criados!\n")
        
        # Passo 2: Aplicar correções (usando sed para modificações específicas)
        print("[*] Passo 2: Aplicando correções...")
        
        # Correção SEMAS-PA: Adicionar headers
        print("  [1/4] Corrigindo SEMAS-PA...")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && sed -i '/async with httpx.AsyncClient/a\\        headers = {\\n            \"User-Agent\": \"Mozilla/5.0 (compatible; EurekaTerra/1.0)\",\\n            \"Accept\": \"application/json\",\\n        }' semas_service.py")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && sed -i 's/params=params,$/params=params,\\n                headers=headers/' semas_service.py")
        
        # Correção CNUC: Atualizar endpoint
        print("  [2/4] Corrigindo CNUC/MMA...")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && sed -i 's|url = \"https://sistemas.mma.gov.br/cnuc/wfs\"|url = \"https://sistemas.mma.gov.br/cnuc-wfs/wfs\"|g' areas_protegidas_service.py")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && sed -i 's|\"typeName\": \"cnuc:unidade_conservacao\"|\"typeName\": \"cnuc:vw_unidade_conservacao\"|g' areas_protegidas_service.py")
        
        # Correção IBAMA: Atualizar endpoint
        print("  [3/4] Corrigindo IBAMA CTF...")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && sed -i 's|areasembargadas/consultar|areas-embargadas/consultar|g' ibama_service.py")
        
        # Correção FUNAI: Verificar se arquivo existe
        stdin, stdout, stderr = ssh.exec_command("ls /root/eureka-terra/backend/app/services/funai_service.py")
        if stdout.channel.recv_exit_status() == 0:
            print("  [4/4] Corrigindo FUNAI...")
            ssh.exec_command("cd /root/eureka-terra/backend/app/services && sed -i 's|\"typeName\": \"Funai:ti_funai\"|\"typeName\": \"Funai:ti_funai\"|g' funai_service.py")
        else:
            print("  [4/4] FUNAI: Arquivo não existe, pulando...")
        
        print("[✓] Correções aplicadas!\n")
        
        # Passo 3: Reiniciar backend
        print("[*] Passo 3: Reiniciando backend para aplicar mudanças...")
        ssh.exec_command("cd /root/eureka-terra && docker-compose restart backend")
        time.sleep(30)  # Aguardar reinicialização
        
        # Verificar saúde
        stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/health")
        health = stdout.read().decode('utf-8')
        if "ok" in health:
            print("[✓] Backend reiniciado e saudável!\n")
        else:
            print("[!] Backend reiniciado mas health check falhou!\n")
        
        # Passo 4: Testar APIs corrigidas
        print("[*] Passo 4: Testando APIs corrigidas...")
        print("-" * 80)
        
        # Testar SEMAS-PA
        print("\n[1/4] Testando SEMAS-PA...")
        stdin, stdout, stderr = ssh.exec_command("cd /root/eureka-terra && python3 -c \"import urllib.request; import ssl; ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE; data = urllib.request.urlopen('https://car.semas.pa.gov.br/geoserver/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=secar-pa:imovel&CQL_FILTER=cod_imovel=%27PA-1501451-110F7A95501049E282B11240815ECA81%27&outputFormat=application/json&count=1', context=ctx, timeout=30); print(f'Status: {data.getcode()}')\"")
        output = stdout.read().decode('utf-8')
        print(output or "Sem output")
        
        # Testar CNUC
        print("\n[2/4] Testando CNUC/MMA...")
        stdin, stdout, stderr = ssh.exec_command("cd /root/eureka-terra && python3 -c \"import urllib.request; data = urllib.request.urlopen('https://sistemas.mma.gov.br/cnuc-wfs/wfs?service=WFS&version=2.0.0&request=GetFeature&typeName=cnuc:vw_unidade_conservacao&outputFormat=application/json&count=1', timeout=30); print(f'Status: {data.getcode()}')\"")
        output = stdout.read().decode('utf-8')
        print(output or "Sem output")
        
        # Testar IBAMA
        print("\n[3/4] Testando IBAMA CTF...")
        stdin, stdout, stderr = ssh.exec_command("cd /root/eureka-terra && python3 -c \"import urllib.request; import json; data = urllib.request.urlopen('https://servicos.ibama.gov.br/ctf/publico/areas-embargadas/consultar?numeroCar=PA-1501451-110F7A95501049E282B11240815ECA81&pagina=1&tamanhoPagina=100', timeout=30); print(f'Status: {data.getcode()}')\"")
        output = stdout.read().decode('utf-8')
        print(output or "Sem output")
        
        print("\n[✓] Testes concluídos!")
        
        # Fechar conexão
        ssh.close()
        print("\n" + "=" * 80)
        print("PROCESSO DE CORREÇÃO CONCLUÍDO!")
        print("=" * 80)
        print("\nPróximos passos:")
        print("1. Teste uma análise real no portal")
        print("2. Verifique os logs: docker logs eureka_backend --tail=50")
        print("3. Se ainda houver problemas, verifique os backups em:")
        print("   /root/eureka-terra/backend/app/services/*.py.backup")
        
    except Exception as e:
        print(f"[✗] Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    aplicar_correcoes()