#!/usr/bin/env python3
"""
Aplica correção de SSL do SICAR na VPS de forma simples
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
        # 1. Fazer backup
        print("[*] Fazendo backup...")
        ssh.exec_command('cd /root/eureka-terra/backend/app/services && cp sicar_service.py sicar_service.py.backup', timeout=10)
        
        # 2. Adicionar import ssl
        print("[*] Adicionando import ssl...")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && sed -i '1a import ssl' sicar_service.py", timeout=10)
        
        # 3. Adicionar contexto SSL antes da função
        print("[*] Adicionando contexto SSL...")
        comando = """cd /root/eureka-terra/backend/app/services && 
        sed -i '/^async def buscar_car_sicar/i # Contexto SSL para contornar problemas de certificado no SICAR\n_ssl_context = ssl.create_default_context()\n_ssl_context.check_hostname = False\n_ssl_context.verify_mode = ssl.CERT_NONE\n' sicar_service.py"""
        ssh.exec_command(comando, timeout=10)
        
        # 4. Substituir verify=False
        print("[*] Atualizando verify=False...")
        ssh.exec_command("cd /root/eureka-terra/backend/app/services && sed -i 's/verify=False, headers=HEADERS/verify=_ssl_context, headers=HEADERS/g' sicar_service.py", timeout=10)
        
        # 5. Verificar
        print("[*] Verificando correção...")
        stdin, stdout, stderr = ssh.exec_command('cd /root/eureka-terra/backend/app/services && grep -c "_ssl_context" sicar_service.py', timeout=10)
        count = stdout.read().decode().strip()
        
        if int(count) > 0:
            print(f"✅ Correção aplicada! ({count} ocorrências)")
        else:
            print("❌ Falha na correção")
            return False
        
        # 6. Rebuild backend
        print("\n[*] Rebuildando backend...")
        stdin, stdout, stderr = ssh.exec_command('cd /root/eureka-terra && docker-compose build --no-cache backend 2>&1 | tail -20', timeout=600)
        print(stdout.read().decode())
        
        # 7. Restart
        print("[*] Restartando backend...")
        ssh.exec_command('cd /root/eureka-terra && docker-compose restart backend', timeout=30)
        time.sleep(10)
        
        print("\n" + "="*80)
        print("✅ CORREÇÃO APLICADA!")
        print("="*80)
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
    finally:
        ssh.close()

if __name__ == "__main__":
    sucesso = aplicar_correcao()
    exit(0 if sucesso else 1)