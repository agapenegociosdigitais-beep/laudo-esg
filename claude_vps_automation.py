#!/usr/bin/env python3
"""
Automação Claude para VPS Eureka Terra
Interface para Claude executar comandos automaticamente
"""

import paramiko
import json
from typing import Optional, Dict, List

class ClaudeVPSAutomation:
    """Automação VPS para Claude"""

    def __init__(self, host="23.106.45.137", user="root", password="JVghqGUersYW6h8Q"):
        self.host = host
        self.user = user
        self.password = password
        self.ssh = None
        self.connected = False

    def connect(self) -> bool:
        """Conecta à VPS"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, username=self.user, password=self.password, timeout=10)
            self.connected = True
            return True
        except Exception as e:
            print(f"Erro de conexão: {e}")
            return False

    def run(self, command: str) -> Dict[str, str]:
        """Executa comando e retorna resultado"""
        if not self.connected:
            return {"error": "Não conectado à VPS"}

        try:
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=300)
            out = stdout.read().decode('utf-8')
            err = stderr.read().decode('utf-8')
            return {"output": out, "error": err, "success": len(err) == 0}
        except Exception as e:
            return {"error": str(e)}

    # ============ COMANDOS SIMPLES ============

    def git_status(self) -> Dict:
        """Estado do git"""
        return self.run("cd /root/eureka-terra && git status")

    def git_pull(self) -> Dict:
        """Pull do main"""
        return self.run("cd /root/eureka-terra && git pull origin main")

    def git_log(self, n=5) -> Dict:
        """Últimos N commits"""
        return self.run(f"cd /root/eureka-terra && git log --oneline -n {n}")

    def git_commit(self, message: str) -> Dict:
        """Fazer commit"""
        return self.run(f"cd /root/eureka-terra && git add -A && git commit -m '{message}'")

    def git_push(self) -> Dict:
        """Push para main"""
        return self.run("cd /root/eureka-terra && git push origin main")

    # ============ DOCKER ============

    def docker_ps(self) -> Dict:
        """Lista containers"""
        return self.run("cd /root/eureka-terra && docker-compose ps")

    def docker_down(self) -> Dict:
        """Para containers"""
        return self.run("cd /root/eureka-terra && docker-compose down")

    def docker_up(self) -> Dict:
        """Sobe containers"""
        result = self.run("cd /root/eureka-terra && docker-compose up -d")
        # Aguarda backend
        self.run("sleep 45")
        return result

    def docker_build(self, service="backend") -> Dict:
        """Rebuilda serviço"""
        return self.run(f"cd /root/eureka-terra && docker-compose build --no-cache {service}")

    def docker_restart(self, service="backend") -> Dict:
        """Reinicia serviço"""
        return self.run(f"cd /root/eureka-terra && docker-compose restart {service}")

    def docker_logs(self, service="backend", lines=50) -> Dict:
        """Logs de um serviço"""
        return self.run(f"cd /root/eureka-terra && docker-compose logs {service} --tail={lines}")

    def health_check(self) -> Dict:
        """Verifica saúde do backend"""
        return self.run("curl -s http://localhost:8000/health")

    # ============ ARQUIVO ============

    def read_file(self, path: str) -> Dict:
        """Lê arquivo"""
        return self.run(f"cat {path}")

    def edit_file_sed(self, path: str, old: str, new: str) -> Dict:
        """Edita arquivo com sed"""
        old_esc = old.replace("'", "'\\''")
        new_esc = new.replace("'", "'\\''")
        cmd = f"sed -i 's|{old_esc}|{new_esc}|g' {path}"
        return self.run(cmd)

    def create_file(self, path: str, content: str) -> Dict:
        """Cria arquivo"""
        content_esc = content.replace("'", "'\\''")
        return self.run(f"cat > {path} << 'EOF'\n{content}\nEOF")

    # ============ DEPLOY AUTOMÁTICO ============

    def full_deploy(self) -> Dict[str, str]:
        """Deploy completo automático"""
        results = {}

        print("[1/5] Git Pull...")
        results["git_pull"] = self.git_pull()["output"][:200]

        print("[2/5] Docker Down...")
        results["docker_down"] = self.docker_down()["output"][:200]

        print("[3/5] Docker Build (esto demora ~3min)...")
        results["docker_build"] = self.docker_build()["output"][-200:]

        print("[4/5] Docker Up...")
        results["docker_up"] = self.docker_up()["output"][:200]

        print("[5/5] Health Check...")
        health = self.health_check()
        results["health_check"] = "OK ✓" if "ok" in health.get("output", "") else "FALHOU ✗"

        return results

    def disconnect(self):
        """Desconecta"""
        if self.ssh:
            self.ssh.close()
            self.connected = False


# ============ FUNÇÕES PARA CLAUDE USAR ============

def vps_execute(command: str) -> str:
    """
    Executa comando na VPS via SSH

    Uso:
        resultado = vps_execute("git status")
        resultado = vps_execute("docker-compose ps")
    """
    client = ClaudeVPSAutomation()
    if not client.connect():
        return "Erro: Não conseguiu conectar à VPS"

    result = client.run(f"cd /root/eureka-terra && {command}")
    client.disconnect()

    if result.get("error"):
        return f"Erro: {result['error']}"
    return result.get("output", "")


def vps_deploy() -> str:
    """Executa deploy completo na VPS"""
    client = ClaudeVPSAutomation()
    if not client.connect():
        return "Erro: Não conseguiu conectar à VPS"

    results = client.full_deploy()
    client.disconnect()

    return json.dumps(results, indent=2)


def vps_git_pull_and_restart() -> str:
    """Pull + Restart automático"""
    client = ClaudeVPSAutomation()
    if not client.connect():
        return "Erro: Não conseguiu conectar à VPS"

    print("[1/3] Git Pull...")
    pull = client.git_pull()

    print("[2/3] Restart Backend...")
    restart = client.docker_restart("backend")

    print("[3/3] Wait + Health Check...")
    client.run("sleep 15")
    health = client.health_check()

    client.disconnect()

    return f"""
    Git Pull: {'OK' if pull['success'] else 'FAILED'}
    Restart: {'OK' if restart['success'] else 'FAILED'}
    Health: {'OK' if 'ok' in health.get('output', '') else 'FAILED'}
    """


def vps_logs(lines: int = 50) -> str:
    """Retorna logs do backend"""
    client = ClaudeVPSAutomation()
    if not client.connect():
        return "Erro: Não conseguiu conectar à VPS"

    logs = client.docker_logs("backend", lines)
    client.disconnect()

    return logs.get("output", "")


if __name__ == "__main__":
    # Teste rápido
    print("Testando conexao VPS...")
    client = ClaudeVPSAutomation()

    if client.connect():
        print("[OK] Conectado!")
        print("\nContainers:")
        ps = client.docker_ps()
        print(ps["output"][:500])

        print("\nHealth:")
        health = client.health_check()
        print(health["output"])

        client.disconnect()
    else:
        print("[ERRO] Falha na conexao")
