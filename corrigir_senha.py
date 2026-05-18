#!/usr/bin/env python3
"""Corrigir hash da senha no banco de dados"""
from claude_vps_automation import ClaudeVPSAutomation

def corrigir_senha():
    print("=" * 80)
    print("CORRIGINDO HASH DA SENHA NO BANCO")
    print("=" * 80)
    
    client = ClaudeVPSAutomation()
    
    if not client.connect():
        print("❌ Falha ao conectar à VPS")
        return False
    
    print("✅ Conectado à VPS")
    print()
    
    # Gerar novo hash bcrypt válido
    print("Gerando novo hash bcrypt para a senha...")
    cmd_gerar = """docker exec eureka_backend python -c "
from app.core.security import get_password_hash
print(get_password_hash('sr 77840000'))
"""
    
    result = client.run(cmd_gerar)
    
    if result['output']:
        hash_novo = result['output'].strip()
        print(f"Novo hash gerado: {hash_novo[:60]}...")
        
        # Atualizar no banco
        print("\nAtualizando hash no banco de dados...")
        cmd_atualizar = f"""docker exec eureka_postgres psql -U eureka -d eureka_db -c "UPDATE usuarios SET senha_hash='{hash_novo}' WHERE email='agapenegociosdigitais@gmail.com';"""
        
        result_update = client.run(cmd_atualizar)
        print("Resultado da atualização:")
        print(result_update['output'])
        
        if 'UPDATE 1' in result_update['output']:
            print("\n✅ Hash atualizado com sucesso!")
            return True
        else:
            print("\n❌ Problema ao atualizar hash")
            return False
    else:
        print("❌ Falha ao gerar novo hash")
        if result['error']:
            print("Erro:", result['error'])
        return False

if __name__ == "__main__":
    corrigir_senha()
