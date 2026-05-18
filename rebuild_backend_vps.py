#!/usr/bin/env python3
"""
Reconstruir backend na VPS para aplicar alterações
"""
from claude_vps_automation import ClaudeVPSAutomation

def rebuild_backend():
    print("=" * 80)
    print("RECONSTRUINDO BACKEND NA VPS")
    print("=" * 80)
    
    client = ClaudeVPSAutomation()
    
    if not client.connect():
        print("❌ Não foi possível conectar à VPS")
        return False
    
    print("✅ Conectado à VPS")
    
    # Parar containers
    print("\n[1] Parando containers...")
    result = client.docker_down()
    print(result['output'])
    
    # Build do backend sem cache
    print("\n[2] Rebuild backend (sem cache)...")
    result = client.docker_build('backend')
    print(result['output'])
    
    # Subir containers novamente
    print("\n[3] Subindo containers...")
    result = client.docker_up()
    print(result['output'])
    
    # Verificar logs
    print("\n[4] Verificando logs do backend...")
    result = client.docker_logs('backend', 20)
    print(result['output'])
    
    print("\n" + "=" * 80)
    print("✅ RECONSTRUÇÃO CONCLUÍDA")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    rebuild_backend()
