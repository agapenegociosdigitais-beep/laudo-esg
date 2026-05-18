---
status: investigating
trigger: "Investigue por que o sistema Eureka Terra na VPS está retornando dados simulados em vez de dados reais das APIs externas (SEMAS-PA, SICAR, PRODES/TerraBrasilis, IBAMA, etc)"
created: 2026-04-22T10:00:00Z
updated: 2026-04-22T10:15:00Z
---

## Current Focus

hypothesis: CONFIRMADA - O sistema retorna dados simulados porque as chamadas às APIs externas governamentais estão falhando na VPS. O código possui múltiplos mecanismos de fallback que disparam simulação quando APIs retornam erro, timeout ou None.
test: Análise completa do código-fonte identificou todos os mecanismos de fallback
expecting: Documentar causa raiz e propor solução
next_action: Finalizar relatório de investigação com causa raiz e recomendações

## Symptoms

expected: O sistema deve sempre consultar APIs externas reais (SEMAS-PA GeoServer, SICAR nacional, TerraBrasilis PRODES, IBAMA CTF, etc) e retornar dados reais

actual: O sistema está retornando dados simulados/fake em vez de dados reais das APIs externas

errors: []

reproduction: Usuário tentou fazer análise de CAR e recebeu dados simulados

started: Desconhecido - usuário reportou recentemente

## Eliminated

## Evidence

- timestamp: 2026-04-22T10:05:00Z
  checked: Análise do car_service.py
  found: Encontrado método _gerar_dado_simulado() que gera dados fake quando nenhuma API responde
  implication: Fallback é acionado quando SEMAS-PA e SICAR nacional falham

- timestamp: 2026-04-22T10:06:00Z
  checked: Análise do desmatamento_service.py
  found: Método verificar_desmatamento() chama _consultar_terrabrasilis() e usa _simular_desmatamento() se retornar None
  implication: PRODES/TerraBrasilis pode estar falhando silenciosamente

- timestamp: 2026-04-22T10:07:00Z
  checked: Análise dos serviços de conformidade
  found: conformidade_service.py tem funções _simular_quilombola() e _simular_assentamento()
  implication: INCRA WFS também pode estar com problemas de conectividade

- timestamp: 2026-04-22T10:08:00Z
  checked: Análise de areas_protegidas_service.py
  found: Métodos _simular_sobreposicao_uc() e _simular_sobreposicao_ti() para CNUC e FUNAI
  implication: APIs de áreas protegidas também têm fallback de simulação

## Resolution

root_cause: |
  O sistema está retornando dados simulados porque as APIs externas governamentais (SEMAS-PA, SICAR, TerraBrasilis, INCRA, CNUC, FUNAI) estão falhando na VPS, e o código possui múltiplos mecanismos de fallback que disparam simulação automaticamente quando as APIs reais falham.
  
  Pontos de fallback identificados:
  1. **car_service.py**: Método `_gerar_dado_simulado()` é chamado quando SEMAS-PA e SICAR nacional falham (linha 129)
  2. **desmatamento_service.py**: Método `_simular_desmatamento()` é chamado quando TerraBrasilis retorna None (linha 63)
  3. **conformidade_service.py**: Funções `_simular_quilombola()` e `_simular_assentamento()` para INCRA WFS (linhas 108, 196)
  4. **areas_protegidas_service.py**: Métodos `_simular_sobreposicao_uc()` e `_simular_sobreposicao_ti()` para CNUC e FUNAI (linhas 146, 174)
  
  As falhas podem ser causadas por:
  - Restrições de rede/firewall na VPS bloqueando chamadas externas
  - Problemas de SSL/TLS mesmo com `verify=False`
  - Timeouts devido a latência alta
  - DNS não resolvendo domínios governamentais
  - Ambiente configurado como `ENVIRONMENT=staging` no .env

fix: |
  1. **Testar conectividade**: Executar script `test_connectivity.py` no container backend para identificar APIs específicas com problemas
  2. **Verificar logs**: Acessar logs do backend na VPS para ver mensagens de erro/warning específicas
  3. **Corrigir conectividade**: 
     - Verificar firewall/rules de segurança da VPS
     - Testar DNS resolution: `docker exec eureka_backend nslookup car.semas.pa.gov.br`
     - Verificar se container pode acessar internet: `docker exec eureka_backend curl -I https://car.semas.pa.gov.br`
  4. **Monitorar**: Adicionar logging detalhado para capturar exceções específicas em cada chamada de API
  5. **Desabilitar fallback (temporário)**: Para debugging, comentar temporariamente as chamadas de simulação para forçar erros visíveis

verification: |
  Após aplicar correções:
  1. Executar análise de CAR e verificar que dados reais são retornados
  2. Confirmar que logs não mostram mais "usando simulacao" ou "fallback simulado"
  3. Validar que todas as APIs externas respondem corretamente

files_changed:
  - backend/test_connectivity.py (criado para diagnóstico)
