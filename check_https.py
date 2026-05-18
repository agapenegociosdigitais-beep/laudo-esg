#!/usr/bin/env python3
"""Verificar configuração HTTPS e certificados SSL"""
import paramiko

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Verificar se existe diretório de certificados
    print("[*] Verificando diretório de certificados...")
    stdin, stdout, stderr = ssh.exec_command("ls -la /root/eureka-terra/certs/ 2>&1", timeout=10)
    certs_dir = stdout.read().decode()
    print("Diretório certs:")
    print(certs_dir)
    
    # Verificar arquivos de certificado
    print("\n[*] Verificando arquivos de certificado...")
    stdin, stdout, stderr = ssh.exec_command("find /root/eureka-terra/certs/ -name '*.crt' -o -name '*.key' -o -name '*.pem' 2>&1", timeout=10)
    cert_files = stdout.read().decode()
    print("Arquivos encontrados:")
    print(cert_files if cert_files else "Nenhum arquivo de certificado encontrado")
    
    # Verificar configuração do nginx
    print("\n[*] Verificando configuração do nginx...")
    stdin, stdout, stderr = ssh.exec_command("grep -A 10 'server_name laudoesg.com' /root/eureka-terra/nginx/nginx.conf", timeout=10)
    nginx_config = stdout.read().decode()
    print("Configuração de server:")
    print(nginx_config if nginx_config else "Configuração não encontrada")
    
    # Verificar se há bloco HTTPS
    print("\n[*] Verificando HTTPS...")
    stdin, stdout, stderr = ssh.exec_command("grep -n 'listen 443' /root/eureka-terra/nginx/nginx.conf", timeout=10)
    https_listen = stdout.read().decode()
    print("HTTPS habilitado:", "SIM" if https_listen else "NÃO")
    
    # Verificar certbot/letsencrypt
    print("\n[*] Verificando Certbot/Letsencrypt...")
    stdin, stdout, stderr = ssh.exec_command("which certbot", timeout=10)
    certbot = stdout.read().decode()
    print("Certbot instalado:", "SIM" if certbot else "NÃO")
    
    ssh.close()
    print("\n[✓] Verificação concluída!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")