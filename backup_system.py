#!/usr/bin/env python3
"""Backup completo do sistema Eureka Terra"""
import paramiko
import datetime
import os

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

# Data para o nome do backup
backup_date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_dir = f"/backups/eureka_terra_{backup_date}"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Criar diretório de backup
    print(f"[*] Criando diretório de backup: {backup_dir}")
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {backup_dir}", timeout=10)
    print(stdout.read().decode())
    
    # 1. Backup do PostgreSQL
    print("\n[*] Fazendo backup do PostgreSQL...")
    pg_backup_file = f"{backup_dir}/postgres_backup.sql"
    pg_cmd = f"docker exec eureka_postgres pg_dump -U eureka eureka_db > {pg_backup_file}"
    stdin, stdout, stderr = ssh.exec_command(pg_cmd, timeout=60)
    pg_result = stdout.read().decode()
    pg_error = stderr.read().decode()
    
    if pg_error:
        print(f"⚠️  Aviso PostgreSQL: {pg_error}")
    else:
        print("✅ Backup PostgreSQL concluído")
    
    # Verificar tamanho do backup PostgreSQL
    stdin, stdout, stderr = ssh.exec_command(f"ls -lh {pg_backup_file}", timeout=10)
    print(f"Tamanho: {stdout.read().decode().strip()}")
    
    # 2. Backup dos arquivos de configuração
    print("\n[*] Fazendo backup dos arquivos de configuração...")
    
    # Copiar arquivos importantes
    arquivos_backup = [
        "/root/eureka-terra/.env",
        "/root/eureka-terra/docker-compose.yml",
        "/root/eureka-terra/nginx/nginx.conf",
        "/root/eureka-terra/backend/requirements.txt",
        "/root/eureka-terra/frontend/package.json"
    ]
    
    for arquivo in arquivos_backup:
        stdin, stdout, stderr = ssh.exec_command(f"cp {arquivo} {backup_dir}/ 2>&1", timeout=10)
        if stderr.read().decode():
            print(f"⚠️  Não foi possível copiar {arquivo}")
        else:
            print(f"✅ {arquivo.split('/')[-1]} copiado")
    
    # 3. Compactar tudo
    print(f"\n[*] Compactando backup...")
    tar_file = f"/backups/eureka_terra_backup_{backup_date}.tar.gz"
    tar_cmd = f"cd /backups && tar -czf {tar_file} eureka_terra_{backup_date}"
    stdin, stdout, stderr = ssh.exec_command(tar_cmd, timeout=30)
    tar_result = stdout.read().decode()
    tar_error = stderr.read().decode()
    
    if tar_error:
        print(f"❌ Erro ao compactar: {tar_error}")
    else:
        print("✅ Backup compactado com sucesso")
    
    # Verificar tamanho do arquivo compactado
    stdin, stdout, stderr = ssh.exec_command(f"ls -lh {tar_file}", timeout=10)
    print(f"\n📦 Arquivo de backup: {stdout.read().decode().strip()}")
    
    # 4. Listar backups existentes
    print("\n[*] Backups existentes:")
    stdin, stdout, stderr = ssh.exec_command("ls -lh /backups/eureka_terra_backup_*.tar.gz 2>&1", timeout=10)
    backups = stdout.read().decode()
    if backups:
        for line in backups.strip().split('\n'):
            print(f"  {line}")
    else:
        print("  Nenhum backup encontrado")
    
    ssh.close()
    print(f"\n[✓] Backup concluído com sucesso!")
    print(f"📁 Local: {tar_file}")
    
except Exception as e:
    print(f"[✗] Erro: {e}")