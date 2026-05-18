#!/usr/bin/env python3
"""
Força rebuild completo do frontend sem cache para garantir que NEXT_PUBLIC_API_URL seja atualizado
"""
import paramiko
import time

def force_clean_rebuild():
    """Força rebuild completo limpando cache do Docker"""
    print("[*] Conectando ao VPS...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('23.106.45.137', username='root', password='JVghqGUersYW6h8Q', timeout=15)
    
    try:
        # 1. Parar e remover containers antigos
        print("[*] Parando e removendo containers antigos...")
        stdin, stdout, stderr = ssh.exec_command('cd /root/eureka-terra && docker-compose down', timeout=30)
        print(stdout.read().decode())
        
        # 2. Limpar cache do Docker
        print("[*] Limpando cache do Docker...")
        stdin, stdout, stderr = ssh.exec_command('docker system prune -af', timeout=60)
        print(stdout.read().decode())
        
        # 3. Remover imagens antigas do frontend especificamente
        print("[*] Removendo imagens antigas do frontend...")
        stdin, stdout, stderr = ssh.exec_command('docker rmi eureka_frontend:latest 2>/dev/null || echo "Imagem não existe"', timeout=30)
        print(stdout.read().decode())
        
        # 4. Verificar .env antes do build
        print("[*] Verificando .env antes do build...")
        stdin, stdout, stderr = ssh.exec_command('cd /root/eureka-terra && grep NEXT_PUBLIC_API_URL .env', timeout=10)
        env_value = stdout.read().decode()
        print(f"Valor no .env: {env_value}")
        
        # 5. Build completo sem cache
        print("[*] Build completo do frontend sem cache...")
        stdin, stdout, stderr = ssh.exec_command(
            'cd /root/eureka-terra && docker-compose build --no-cache --force-rm frontend 2>&1 | tail -50', 
            timeout=600
        )
        build_output = stdout.read().decode()
        print("Últimas linhas do build:")
        print(build_output)
        
        # 6. Subir todos os serviços
        print("[*] Subindo todos os serviços...")
        stdin, stdout, stderr = ssh.exec_command('cd /root/eureka-terra && docker-compose up -d', timeout=60)
        print(stdout.read().decode())
        
        # 7. Aguardar inicialização
        print("[*] Aguardando inicialização...")
        time.sleep(10)
        
        # 8. Verificar variável no container
        print("[*] Verificando variável no container...")
        stdin, stdout, stderr = ssh.exec_command('docker exec eureka_frontend env | grep NEXT_PUBLIC_API_URL', timeout=10)
        container_env = stdout.read().decode()
        print(f"Variável no container: {container_env}")
        
        if 'https://laudoesg.com' in container_env:
            print("\n[V] SUCESSO! O container está usando HTTPS!")
            return True
        else:
            print("\n[X] FALHA! O container ainda está usando HTTP!")
            return False
            
    finally:
        ssh.close()

if __name__ == "__main__":
    success = force_clean_rebuild()
    exit(0 if success else 1)