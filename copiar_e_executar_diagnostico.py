#!/usr/bin/env python3
"""
Copia o script de diagnóstico para a VPS e executa
"""

import paramiko
import sys
import time

# Configurações da VPS
VPS_HOST = "23.106.45.137"
VPS_USER = "root"
VPS_PASS = "JVghqGUersYW6h8Q"

def copiar_e_executar():
    """Copia arquivo e executa diagnóstico"""
    
    print("=" * 80)
    print("CONECTANDO À VPS")
    print("=" * 80)
    
    try:
        # Conectar
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print(f"[*] Conectando em {VPS_HOST}...")
        ssh.connect(VPS_HOST, username=VPS_USER, password=VPS_PASS, timeout=10)
        print("[✓] Conectado!\n")
        
        # Abrir SFTP
        print("[*] Abrindo conexão SFTP...")
        sftp = ssh.open_sftp()
        
        # Copiar arquivo
        print("[*] Copiando diagnosticar_apis_vps_simples.py...")
        sftp.put(
            "diagnosticar_apis_vps_simples.py",
            "/root/eureka-terra/diagnosticar_apis_vps_simples.py"
        )
        print("[✓] Arquivo copiado!\n")
        
        # Fechar SFTP
        sftp.close()
        
        # Executar diagnóstico
        print("[*] Executando diagnóstico de APIs...")
        print("-" * 80)
        
        stdin, stdout, stderr = ssh.exec_command(
            "cd /root/eureka-terra && python3 diagnosticar_apis_vps_simples.py",
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
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    copiar_e_executar()