#!/usr/bin/env python3
"""
Script para remover completamente todas as simulações do sistema
Apenas dados reais serão permitidos
"""
import os
import re

def remover_simulacoes():
    """Remove todas as funções e chamadas de simulação"""
    
    services_dir = "C:\\Users\\benja\\Desktop\\eureka-terra\\backend\\app\\services"
    
    files_to_process = [
        'areas_protegidas_service.py',
        'conformidade_service.py', 
        'desmatamento_service.py',
        'embargos_service.py'
    ]
    
    for filename in files_to_process:
        filepath = os.path.join(services_dir, filename)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_len = len(content)
        
        # 1. Remover funções _simular_*
        content = re.sub(r'def _simular_.*?(?=\n    def |\nclass |\Z)', '', content, flags=re.DOTALL)
        
        # 2. Substituir fallbacks por erros explícitos
        
        # Para desmatamento
        content = re.sub(
            r'# ERRO se TerraBrasilis indisponivel.*?raise Exception\(.*?\)',
            '''# ERRO se TerraBrasilis indisponivel - NÃO usar simulação
        logger.error("TerraBrasilis indisponivel - NÃO FOI POSSÍVEL VERIFICAR DESMATAMENTO REAL")
        raise Exception("PRODES/INPE (TerraBrasilis) indisponível. Não é possível verificar desmatamento sem dados reais.")''',
            content,
            flags=re.DOTALL
        )
        
        # Para áreas protegidas
        content = re.sub(
            r'return None  # Deixa o chamador decidir',
            'raise Exception(f"{self.__class__.__name__}: Não foi possível obter dados reais de " + tipo_verificacao)',
            content
        )
        
        # Para conformidade
        content = re.sub(
            r'return \{"sobreposicao": False, "total": 0,.*\}',
            'raise Exception(f"{self.__class__.__name__}: Não foi possível obter dados reais")',
            content,
            flags=re.DOTALL
        )
        
        # 3. Remover imports não utilizados de simulação
        content = re.sub(r'import hashlib\n', '', content)
        content = re.sub(r'from datetime import date, timedelta\n', 'from datetime import date\n', content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'✅ {filename}: {original_len} -> {len(content)} bytes ({original_len-len(content)} removidos)')
    
    print('\n🎉 Todas as simulações removidas com sucesso!')
    print('🎯 O sistema agora retorna apenas DADOS REAIS ou ERROS explícitos')

if __name__ == '__main__':
    remover_simulacoes()
