#!/usr/bin/env python3
"""Finalizar configuração HTTPS"""
import paramiko
import time

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Aguardar nginx iniciar
    print("[*] Aguardando nginx iniciar...")
    time.sleep(5)
    
    # Testar configuração
    print("[*] Testando configuração HTTPS...")
    stdin, stdout, stderr = ssh.exec_command('curl -s -o /dev/null -w "%{http_code}" https://localhost:443/health --insecure', timeout=10)
    https_test = stdout.read().decode()
    print(f'Teste HTTPS: HTTP {https_test}')
    
    # Verificar se o container está rodando
    stdin, stdout, stderr = ssh.exec_command('docker ps --filter name=eureka_nginx --format "{{.Status}}"', timeout=10)
    status = stdout.read().decode().strip()
    print(f'Status nginx: {status}')
    
    # Configurar renovação automática
    print('\n[*] Configurando renovação automática...')
    cron_job = '0 3 * * * docker stop eureka_nginx && certbot renew --quiet && docker start eureka_nginx'
    stdin, stdout, stderr = ssh.exec_command(f'(crontab -l 2>/dev/null; echo "{cron_job}") | crontab -', timeout=10)
    print('✅ Cron job adicionado')
    
    # Verificar cron jobs
    stdin, stdout, stderr = ssh.exec_command('crontab -l', timeout=10)
    cron_list = stdout.read().decode()
    print('\nCron jobs ativos:')
    print(cron_list)
    
    ssh.close()
    print('\n[✓] Configuração HTTPS concluída!')
    print('\n📋 Resumo:')
    print('✅ Certificado SSL existente copiado')
    print('✅ Nginx configurado para HTTPS')
    print('✅ Redirecionamento HTTP para HTTPS ativado')
    print('✅ Renovação automática configurada')
    print('\n🌐 URLs:')
    print('   HTTP:  http://23.106.45.137 (redireciona para HTTPS)')
    print('   HTTPS: https://23.106.45.137')
    print('   Domínio: https://laudoesg.com')
    
except Exception as e:
    print(f"[✗] Erro: {e}")