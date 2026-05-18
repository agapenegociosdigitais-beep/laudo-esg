#!/usr/bin/env python3
"""Upload do arquivo corrigido via SSH e copiar para container"""
import paramiko

HOST = '23.106.45.137'
USER = 'root'
PASSWORD = 'JVghqGUersYW6h8Q'

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)

print('=== FAZENDO UPLOAD DO ARQUIVO CORRIGIDO ===')

# Usar SFTP para fazer upload do arquivo
sftp = ssh.open_sftp()
sftp.put('semas_service_corrigido.py', '/tmp/semas_service_corrigido.py')
sftp.close()
print('[✓] Arquivo enviado para /tmp/semas_service_corrigido.py')

# Copiar do host para o container
cmd = 'docker cp /tmp/semas_service_corrigido.py eureka_backend:/app/app/services/semas_service.py'
stdin, stdout, stderr = ssh.exec_command(cmd)
error = stderr.read().decode()
if error:
    print(f'[!] Erro ao copiar para container: {error}')
else:
    print('[✓] Arquivo copiado para o container!')

# Verificar se o arquivo foi copiado corretamente
print('\n=== VERIFICANDO ARQUIVO NO CONTAINER ===')
cmd = 'docker exec eureka_backend sed -n 67,72p /app/app/services/semas_service.py'
stdin, stdout, stderr = ssh.exec_command(cmd)
result = stdout.read().decode()
print(result)

# Limpar arquivo temporário
ssh.exec_command('rm /tmp/semas_service_corrigido.py')

ssh.close()

print('\n=== REINICIANDO CONTAINER BACKEND ===')
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
cmd = 'docker restart eureka_backend'
stdin, stdout, stderr = ssh.exec_command(cmd)
print('Container reiniciado!')
ssh.close()

print('\n✅ Processo concluído!')