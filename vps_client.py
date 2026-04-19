#!/usr/bin/env python3
"""
VPS SSH Client para Eureka Terra
Permite executar comandos na VPS sem intervenção manual
"""

import paramiko
import sys
import time
from pathlib import Path

class VPSClient:
    """Cliente SSH para VPS Eureka Terra"""

    def __init__(self, host="23.106.45.137", user="root", password="JVghqGUersYW6h8Q", port=22):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.ssh = None
        self.connected = False

    def connect(self):
        """Conecta à VPS"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            print(f"[*] Conectando em {self.user}@{self.host}:{self.port}...")
            self.ssh.connect(
                self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                timeout=10
            )
            self.connected = True
            print("[✓] Conectado à VPS!")
            return True
        except Exception as e:
            print(f"[✗] Erro ao conectar: {e}")
            return False

    def exec_command(self, cmd, show_output=True):
        """Executa comando na VPS"""
        if not self.connected:
            print("[✗] Não conectado à VPS")
            return None

        try:
            print(f"\n[>] Executando: {cmd}")
            stdin, stdout, stderr = self.ssh.exec_command(cmd, timeout=300)

            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')

            if show_output and output:
                print(output)
            if error:
                print(f"[!] Erro: {error}")

            return output
        except Exception as e:
            print(f"[✗] Erro ao executar comando: {e}")
            return None

    def git_pull(self):
        """Faz git pull da branch main"""
        print("\n[=] FASE 1: Git Pull")
        return self.exec_command("cd /root/eureka-terra && git pull origin main")

    def docker_down(self):
        """Para containers"""
        print("\n[=] FASE 2: Docker Down")
        return self.exec_command("cd /root/eureka-terra && docker-compose down")

    def docker_build(self, service="backend"):
        """Rebuilda um serviço (padrão: backend)"""
        print(f"\n[=] FASE 3: Docker Build {service}")
        return self.exec_command(f"cd /root/eureka-terra && docker-compose build --no-cache {service}")

    def docker_up(self):
        """Sobe containers"""
        print("\n[=] FASE 4: Docker Up")
        self.exec_command("cd /root/eureka-terra && docker-compose up -d")

        print("[*] Aguardando 45 segundos para backend inicializar...")
        time.sleep(45)

        return self.health_check()

    def health_check(self):
        """Verifica saúde do backend"""
        print("\n[=] FASE 5: Health Check")
        output = self.exec_command("curl -s http://localhost:8000/health")

        if output and "ok" in output:
            print("[✓] Backend respondendo OK!")
            return True
        else:
            print("[✗] Backend não respondendo!")
            return False

    def docker_ps(self):
        """Lista containers"""
        print("\n[=] Containers Status")
        return self.exec_command("cd /root/eureka-terra && docker-compose ps")

    def logs(self, service="backend", lines=50):
        """Mostra logs de um serviço"""
        print(f"\n[=] Logs de {service}")
        return self.exec_command(f"cd /root/eureka-terra && docker-compose logs {service} --tail={lines}")

    def deploy(self, build_service="backend"):
        """Executa deploy completo"""
        print("\n" + "="*60)
        print("DEPLOY COMPLETO EUREKA TERRA")
        print("="*60)

        steps = [
            ("Git Pull", self.git_pull),
            ("Docker Down", self.docker_down),
            ("Docker Build", lambda: self.docker_build(build_service)),
            ("Docker Up", self.docker_up),
            ("Status", self.docker_ps),
        ]

        for step_name, step_func in steps:
            try:
                result = step_func()
                if not result:
                    print(f"[✗] Falha em {step_name}")
                    return False
            except Exception as e:
                print(f"[✗] Erro em {step_name}: {e}")
                return False

        print("\n" + "="*60)
        print("[✓] DEPLOY CONCLUÍDO COM SUCESSO!")
        print("="*60)
        return True

    def edit_file(self, file_path, old_text, new_text):
        """Edita arquivo na VPS via sed"""
        print(f"\n[*] Editando: {file_path}")

        # Escapar caracteres especiais para sed
        old_text_escaped = old_text.replace('/', '\\/').replace('\n', '\\n')
        new_text_escaped = new_text.replace('/', '\\/').replace('\n', '\\n')

        cmd = f"sed -i 's/{old_text_escaped}/{new_text_escaped}/' {file_path}"
        return self.exec_command(cmd)

    def restart_backend(self):
        """Reinicia apenas o backend"""
        print("\n[*] Reiniciando backend...")
        self.exec_command("cd /root/eureka-terra && docker-compose restart backend")
        time.sleep(10)
        return self.health_check()

    def disconnect(self):
        """Desconecta da VPS"""
        if self.ssh:
            self.ssh.close()
            self.connected = False
            print("\n[✓] Desconectado da VPS")


def main():
    """Menu principal"""

    # Verificar se Paramiko está instalado
    try:
        import paramiko
    except ImportError:
        print("[✗] Paramiko não instalado!")
        print("[*] Instale com: pip install paramiko")
        sys.exit(1)

    client = VPSClient()

    if not client.connect():
        sys.exit(1)

    print("\n" + "="*60)
    print("VPS CLIENT - Eureka Terra")
    print("="*60)
    print("\nOpções:")
    print("1. Deploy Completo (recomendado)")
    print("2. Git Pull")
    print("3. Docker Down")
    print("4. Docker Build Backend")
    print("5. Docker Up")
    print("6. Health Check")
    print("7. Ver Containers")
    print("8. Ver Logs Backend")
    print("9. Restart Backend")
    print("0. Sair")
    print()

    while True:
        choice = input(">>> Escolha uma opção (0-9): ").strip()

        if choice == "1":
            client.deploy()
        elif choice == "2":
            client.git_pull()
        elif choice == "3":
            client.docker_down()
        elif choice == "4":
            client.docker_build()
        elif choice == "5":
            client.docker_up()
        elif choice == "6":
            client.health_check()
        elif choice == "7":
            client.docker_ps()
        elif choice == "8":
            client.logs()
        elif choice == "9":
            client.restart_backend()
        elif choice == "0":
            break
        else:
            print("[✗] Opção inválida!")

    client.disconnect()


if __name__ == "__main__":
    main()
