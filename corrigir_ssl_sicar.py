#!/usr/bin/env python3
"""
Corrige o problema de SSL Handshake no SICAR Nacional
"""
import ssl
import sys
import os

# Caminho para o sicar_service.py
SICAR_SERVICE_PATH = "c:\\Users\\benja\\Desktop\\eureka-terra\\backend\\app\\services\\sicar_service.py"

def corrigir_ssl():
    """Adiciona contexto SSL customizado ao sicar_service.py"""
    
    print("=" * 80)
    print("CORREÇÃO DE SSL - SICAR NACIONAL")
    print("=" * 80)
    
    # Ler arquivo atual
    with open(SICAR_SERVICE_PATH, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Verificar se já tem a correção
    if "ssl.create_default_context()" in conteudo:
        print("✅ Correção já aplicada!")
        return True
    
    # Adicionar imports no início do arquivo
    if "import ssl" not in conteudo:
        # Encontrar onde adicionar (depois dos imports iniciais)
        linhas = conteudo.split('\n')
        import_idx = 0
        for i, linha in enumerate(linhas):
            if linha.startswith('import ') or linha.startswith('from '):
                import_idx = i
        
        # Adicionar import ssl
        linhas.insert(import_idx + 1, "import ssl")
        conteudo = '\n'.join(linhas)
        print("✅ Adicionado 'import ssl'")
    
    # Adicionar contexto SSL antes da função buscar_car_sicar
    contexto_ssl = '''
# Contexto SSL para contornar problemas de certificado no SICAR
_ssl_context = ssl.create_default_context()
_ssl_context.check_hostname = False
_ssl_context.verify_mode = ssl.CERT_NONE

'''
    
    if "_ssl_context = ssl.create_default_context()" not in conteudo:
        # Encontrar a função buscar_car_sicar
        idx = conteudo.find("async def buscar_car_sicar")
        if idx > 0:
            conteudo = conteudo[:idx] + contexto_ssl + conteudo[idx:]
            print("✅ Adicionado contexto SSL customizado")
    
    # Substituir verify=False por verify=_ssl_context
    conteudo = conteudo.replace(
        'verify=False, headers=HEADERS',
        'verify=_ssl_context, headers=HEADERS'
    )
    print("✅ Atualizado verify=False para usar contexto SSL")
    
    # Salvar arquivo modificado
    with open(SICAR_SERVICE_PATH, 'w', encoding='utf-8') as f:
        f.write(conteudo)
    
    print("\n" + "=" * 80)
    print("✅ CORREÇÃO APLICADA COM SUCESSO!")
    print("=" * 80)
    print("\nPróximos passos:")
    print("1. Rebuild do backend: docker-compose build --no-cache backend")
    print("2. Restart dos serviços: docker-compose restart backend")
    print("3. Testar novamente com o CAR real")
    
    return True

if __name__ == "__main__":
    try:
        corrigir_ssl()
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)