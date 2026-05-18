#!/usr/bin/env python3
"""Corrigir arquivo semas_service.py no container"""
import paramiko

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

# Conteúdo correto para as linhas 68-75
codigo_correto = '''    try:
        async with httpx.AsyncClient(
            timeout=20, verify=False, headers=HEADERS
        ) as client:'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

print('=== CORRIGINDO ARQUIVO SEMAS_SERVICE.PY ===')

# Criar script Python para corrigir o arquivo dentro do container
script_correcao = f'''
import sys

# Ler o arquivo original
with open('/app/app/services/semas_service.py', 'r') as f:
    linhas = f.readlines()

# Verificar e corrigir as linhas 68-75 (índice 67-74)
if len(linhas) > 74:
    print(f'Linha 68 (original): {{linhas[67].rstrip()}}')
    print(f'Linha 69 (original): {{linhas[68].rstrip()}}')
    print(f'Linha 70 (original): {{linhas[69].rstrip()}}')
    print(f'Linha 71 (original): {{linhas[70].rstrip()}}')
    print(f'Linha 72 (original): {{linhas[71].rstrip()}}')
    print(f'Linha 73 (original): {{linhas[72].rstrip()}}')
    print(f'Linha 74 (original): {{linhas[73].rstrip()}}')
    print(f'Linha 75 (original): {{linhas[74].rstrip()}}')
    
    # Substituir as linhas corrompidas
    linhas[67] = '    try:\n'
    linhas[68] = '        async with httpx.AsyncClient(\n'
    linhas[69] = '            timeout=20, verify=False, headers=HEADERS\n'
    linhas[70] = '        ) as client:\n'
    
    # Remover as linhas extras (71-74)
    del linhas[71:75]
    
    print('\\n=== APÓS CORREÇÃO ===')
    print(f'Linha 68 (corrigida): {{linhas[67].rstrip()}}')
    print(f'Linha 69 (corrigida): {{linhas[68].rstrip()}}')
    print(f'Linha 70 (corrigida): {{linhas[69].rstrip()}}')
    print(f'Linha 71 (corrigida): {{linhas[70].rstrip()}}')
    
    # Salvar o arquivo corrigido
    with open('/app/app/services/semas_service.py', 'w') as f:
        f.writelines(linhas)
    
    print('\\n✅ Arquivo corrigido com sucesso!')
else:
    print('❌ Arquivo não tem linhas suficientes')
'''

# Salvar script no host
cmd = f"cat > /tmp/fix_semas.py << 'EOF'\n{script_correcao}\nEOF"
stdin, stdout, stderr = ssh.exec_command(cmd)

# Copiar para o container
cmd = "docker cp /tmp/fix_semas.py eureka_backend:/tmp/fix_semas.py"
stdin, stdout, stderr = ssh.exec_command(cmd)

# Executar correção no container
cmd = "docker exec eureka_backend python /tmp/fix_semas.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

# Limpar
ssh.exec_command("rm /tmp/fix_semas.py")
ssh.exec_command("docker exec eureka_backend rm /tmp/fix_semas.py")

# Verificar se a correção funcionou
print('\n=== VERIFICANDO CORREÇÃO ===')
cmd = "docker exec eureka_backend sed -n 67,72p /app/app/services/semas_service.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

ssh.close()

print('\n✅ Correção concluída!')
print('Reiniciando container backend...')

# Reiniciar container para aplicar mudanças
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
cmd = "docker restart eureka_backend"
stdin, stdout, stderr = ssh.exec_command(cmd)
print('Container reiniciado!')
ssh.close()