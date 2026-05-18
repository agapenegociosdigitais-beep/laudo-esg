#!/usr/bin/env python3
"""
Executa diagnóstico de APIs diretamente na VPS e mostra output completo
"""

import paramiko
import sys
import time

# Configurações da VPS
VPS_HOST = "23.106.45.137"
VPS_USER = "root"
VPS_PASS = "JVghqGUersYW6h8Q"

def executar_diagnostico():
    """Conecta na VPS e executa o diagnóstico"""
    
    print("=" * 80)
    print("CONECTANDO À VPS E EXECUTANDO DIAGNÓSTICO")
    print("=" * 80)
    
    try:
        # Conectar
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"[*] Conectando em {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("[✓] Conectado!\n")
        
        # Executar diagnóstico
        print("[*] Executando diagnóstico de APIs...")
        print("-" * 80)
        
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/eureka-terra && python3 diagnosticar_apis_vps.py",
            timeout=300
        )
        
        # Ler output em tempo real
        while not stdout.channel.exit_status_ready():
            if stdout.channel.recv_ready():
                output = stdout.channel.recv(1024).decode('utf-8')
                print(output, end='', flush=True)
            time.sleep(0.1)
        
        # Ler output final
        output_final = stdout.read().decode('utf-8')
        erro_final = stderr.read().decode('utf-8')
        
        if output_final:
            print(output_final)
        if erro_final:
            print("[!] Erros:", erro_final)
        
        # Fechar conexão
        ssh.close()
        print("\n[✓] Diagnóstico concluído!")
        
    except Exception as e:
        print(f"[✗] Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    executar_diagnostico()