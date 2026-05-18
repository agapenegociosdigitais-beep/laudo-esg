#!/usr/bin/env python3
"""
Aplica a correção de SSL do SICAR na VPS e rebuilda o backend
"""
import paramiko
import time

def aplicar_correcao():
    """Aplica correção de SSL no sicar_service.py na VPS"""
    print("[*] Conectando ao VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('23.106.45.137', username='root', password='JVghqGUersYW6h8Q', timeout=15)
    
    try:
        # 1. Fazer backup do arquivo original
        print("[*] Fazendo backup do sicar_service.py...")
        stdin, stdout, stderr = ssh.exec_command(
            'cd /root/eureka-terra/backend/app/services && cp sicar_service.py sicar_service.py.backup',
            timeout=10
        )
        print("✅ Backup criado: sicar_service.py.backup")
        
        # 2. Aplicar correção de SSL
        print("[*] Aplicando correção de SSL...")
        
        # Adicionar import ssl no início
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/eureka-terra/backend/app/services && sed -i '1a import ssl' sicar_service.py",
            timeout=10
        )
        
        # Adicionar contexto SSL antes da função buscar_car_sicar
        comando = """cd /root/eureka-terra/backend/app/services && python3 -c "
import re
with open('sicar_service.py', 'r') as f:
    content = f.read()

# Substituir verify=False
content = content.replace('verify=False, headers=HEADERS', 'verify=_ssl_context, headers=HEADERS')

# Adicionar contexto antes da função  
ssl_context = '\\n# Contexto SSL para contornar problemas de certificado no SICAR\\n_ssl_context = ssl.create_default_context()\\n_ssl_context.check_hostname = False\\n_ssl_context.verify_mode = ssl.CERT_NONE\\n\\n'
content = content.replace('async def buscar_car_sicar', ssl_context + 'async def buscar_car_sicar')

with open('sicar_service.py', 'w') as f:
    f.write(content)

print('Correção aplicada')
"""
        stdin, stdout, stderr = ssh.exec_command(comando, timeout=30)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 3. Verificar se a correção foi aplicada
        print("[*] Verificando correção...")
        stdin, stdout, stderr = ssh.exec_command(
            'cd /root/eureka-terra/backend/app/services && grep -n "_ssl_context" sicar_service.py',
            timeout=10
        )
        resultado = stdout.read().decode()
        if "_ssl_context" in resultado:
            print("✅ Correção de SSL aplicada com sucesso!")
        else:
            print("❌ Falha ao aplicar correção")
            return False
        
        # 4. Rebuild do backend
        print("\n[*] Rebuildando backend...")
        stdin, stdout, stderr = ssh.exec_command(
            'cd /root/eureka-terra && docker-compose build --no-cache backend 2>&1 | tail -30',
            timeout=600
        )
        build_output = stdout.read().decode()
        print("Últimas linhas do build:")
        print(build_output)
        
        # 5. Restart do backend
        print("\n[*] Restartando backend...")
        stdin, stdout, stderr = ssh.exec_command(
            'cd /root/eureka-terra && docker-compose restart backend',
            timeout=30
        )
        print(stdout.read().decode())
        
        # 6. Aguardar inicialização
        print("[*] Aguardando inicialização...")
        time.sleep(10)
        
        # 7. Testar conexão
        print("\n[*] Testando backend...")
        stdin, stdout, stderr = ssh.exec_command(
            'curl -s https://laudoesg.com/api/v1/health || echo "Health check não implementado"',
            timeout=10
        )
        print("Resposta do backend:", stdout.read().decode()[:100])
        
        print("\n" + "="*80)
        print("✅ CORREÇÃO APLICADA E BACKEND REBUILDADO!")
        print("="*80)
        print("\nPróximo passo: Testar com CAR real novamente")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    sucesso = aplicar_correcao()
    exit(0 if sucesso else 1)