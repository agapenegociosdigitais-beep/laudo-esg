#!/usr/bin/env python3
"""
Executa diagnóstico na VPS, salva em arquivo e copia de volta
"""

import paramiko
import sys
import time
from pathlib import Path

# Configurações da VPS
VPS_HOST = "23.106.45.137"
VPS_USER = "root"
VPS_PASS = "JVghqGUersYW6h8Q"

def executar_diagnostico_completo():
    """Executa diagnóstico na VPS e copia resultado de volta"""
    
    print("=" * 80)
    print("EXECUTANDO DIAGNÓSTICO COMPLETO NA VPS")
    print("=" * 80)
    
    try:
        # Conectar
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"[*] Conectando em {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("[✓] Conectado!\n")
        
        # Passo 1: Executar diagnóstico e salvar output
        print("[*] Passo 1: Executando diagnóstico na VPS...")
        print("-" * 80)
        
        # Comando para executar diagnóstico e salvar em arquivo
        comando = """
cd /root/eureka-terra
python3 diagnosticar_apis_vps_simples.py > diagnostico_output.log 2>&1
echo "=== FIM DO DIAGNÓSTICO ===" >> diagnostico_output.log
cat diagnostico_output.log
"""
        
        stdin, stdout, stderr = ssh.exec_command(comando, timeout=300)
        
        # Ler output em tempo real
        output_completo = ""
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                chunk = stdout.channel.recv(4096).decode('utf-8')
                print(chunk, end='', flush=True)
                output_completo += chunk
            time.sleep(0.1)
        
        # Ler restante do output
        output_final = stdout.read().decode('utf-8')
        erro_final = stderr.read().decode('utf-8')
        
        if output_final:
            print(output_final)
            output_completo += output_final
        if erro_final:
            print("[!] Erros:", erro_final)
        
        print("\n[✓] Diagnóstico executado na VPS!\n")
        
        # Passo 2: Copiar arquivo JSON de volta
        print("[*] Passo 2: Copiando resultado de volta...")
        
        sftp = ssh.open_sftp()
        arquivo_remoto = "/root/eureka-terra/diagnostico_apis_vps_simples.json"
        arquivo_local = "diagnostico_apis_vps_resultado_final.json"
        
        try:
            sftp.get(arquivo_remoto, arquivo_local)
            print(f"[✓] Arquivo copiado: {arquivo_local}")
            
            # Ler e mostrar conteúdo do arquivo
            with open(arquivo_local, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                print("\n" + "=" * 80)
                print("RESULTADO DO DIAGNÓSTICO (JSON)")
                print("=" * 80)
                print(conteudo[:2000])  # Mostrar primeiros 2000 chars
                
        except FileNotFoundError:
            print(f"[!] Arquivo {arquivo_remoto} não encontrado na VPS")
        
        sftp.close()
        
        # Passo 3: Verificar se há arquivo de log
        print("\n[*] Passo 3: Verificando arquivo de log...")
        try:
            sftp = ssh.open_sftp()
            arquivo_log = "/root/eureka-terra/diagnostico_output.log"
            log_local = "diagnostico_output.log"
            
            sftp.get(arquivo_log, log_local)
            print(f"[✓] Log copiado: {log_local}")
            
            with open(log_local, 'r', encoding='utf-8') as f:
                log_conteudo = f.read()
                print("\n" + "=" * 80)
                print("LOG COMPLETO DO DIAGNÓSTICO")
                print("=" * 80)
                print(log_conteudo)
                
            sftp.close()
        except:
            print("[!] Arquivo de log não encontrado")
        
        # Fechar conexão SSH
        ssh.close()
        
        print("\n" + "=" * 80)
        print("PROCESSO CONCLUÍDO!")
        print("=" * 80)
        
    except Exception as e:
        print(f"[✗] Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    executar_diagnostico_completo()