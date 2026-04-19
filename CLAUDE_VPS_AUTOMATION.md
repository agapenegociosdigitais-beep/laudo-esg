# 🤖 AUTOMAÇÃO CLAUDE VPS - EUREKA TERRA

## 📋 O QUE FOI CRIADO

Dois scripts Python que permitem **CLAUDE EXECUTAR COMANDOS NA VPS AUTOMATICAMENTE**:

1. **`vps_client.py`** - Menu interativo (para você usar manualmente)
2. **`claude_vps_automation.py`** - Interface programática (para Claude usar)

---

## 🚀 COMO FUNCIONA

### **Instalação de Dependências**

Execute no seu PC (uma única vez):

```bash
pip install paramiko
```

---

## 📝 COMO USAR COM CLAUDE

### **Opção 1: Execute um Comando Simples**

Diga ao Claude:
```
Execute na VPS: git pull origin main
```

Claude vai executar:
```python
from claude_vps_automation import vps_execute
resultado = vps_execute("git pull origin main")
```

---

### **Opção 2: Deploy Automático Completo**

Diga ao Claude:
```
Faça deploy completo na VPS (git pull + docker build + docker up)
```

Claude vai executar:
```python
from claude_vps_automation import vps_deploy
resultado = vps_deploy()
```

---

### **Opção 3: Git Pull + Restart**

Diga ao Claude:
```
Faz pull do código novo e reinicia o backend
```

Claude vai executar:
```python
from claude_vps_automation import vps_git_pull_and_restart
resultado = vps_git_pull_and_restart()
```

---

### **Opção 4: Ver Logs**

Diga ao Claude:
```
Mostra últimos 100 logs do backend
```

Claude vai executar:
```python
from claude_vps_automation import vps_logs
resultado = vps_logs(lines=100)
```

---

## 🎯 EXEMPLOS DE USO

### **Modificar Arquivo na VPS**

```
Claude, edite o arquivo /root/eureka-terra/nginx/nginx.conf
e mude "porta 8080" para "porta 9090"
```

Claude vai:
```python
from claude_vps_automation import ClaudeVPSAutomation

client = ClaudeVPSAutomation()
client.connect()
client.edit_file_sed(
    "/root/eureka-terra/nginx/nginx.conf",
    "porta 8080",
    "porta 9090"
)
client.disconnect()
```

---

### **Fazer Commit Automático**

```
Claude, faça commit na VPS com mensagem:
"Fix: corrigir nginx para porta 9090"
```

Claude vai:
```python
from claude_vps_automation import ClaudeVPSAutomation

client = ClaudeVPSAutomation()
client.connect()
client.git_commit("Fix: corrigir nginx para porta 9090")
client.git_push()
client.disconnect()
```

---

### **Monitorar Backend**

```
Claude, verifique a saúde do backend e se os containers estão up
```

Claude vai:
```python
from claude_vps_automation import ClaudeVPSAutomation

client = ClaudeVPSAutomation()
client.connect()
ps = client.docker_ps()
health = client.health_check()
client.disconnect()
```

---

## 📚 REFERÊNCIA COMPLETA DE COMANDOS

### **GIT**
```
vps_git_pull() - Pull do main
vps_git_status() - Status
vps_git_log(n=5) - Últimos N commits
vps_git_commit(msg) - Fazer commit
vps_git_push() - Push
```

### **DOCKER**
```
vps_docker_ps() - Ver containers
vps_docker_down() - Parar
vps_docker_up() - Subir
vps_docker_build(service) - Rebuild serviço
vps_docker_restart(service) - Reiniciar
vps_docker_logs(service, lines) - Ver logs
```

### **ARQUIVO**
```
vps_read_file(path) - Ler arquivo
vps_edit_file_sed(path, old, new) - Editar com sed
vps_create_file(path, content) - Criar arquivo
```

### **HEALTH**
```
vps_health_check() - Verificar saúde
```

### **AUTO**
```
vps_deploy() - Deploy completo
vps_git_pull_and_restart() - Pull + restart
vps_logs(lines) - Logs
```

---

## 🔐 CREDENCIAIS (HARDCODED)

```python
host = "23.106.45.137"
user = "root"
password = "JVghqGUersYW6h8Q"
```

⚠️ **IMPORTANTE:** Não compartilhe este arquivo publicamente!

---

## ✅ EXEMPLO DE WORKFLOW

### **Cenário: Você quer fazer um pequeno fix e deployar**

**Você (em linguagem natural):**
```
Claude, faz assim:
1. Edita o arquivo /root/eureka-terra/backend/app/main.py
   muda "DEBUG = True" para "DEBUG = False"
2. Faz commit com mensagem "Fix: disable debug mode"
3. Faz push
4. Faz deploy completo na VPS
5. Verifica se backend está respondendo
6. Mostra status dos containers
```

**Claude vai:**
```python
from claude_vps_automation import ClaudeVPSAutomation

client = ClaudeVPSAutomation()
client.connect()

# 1. Editar
client.edit_file_sed(
    "/root/eureka-terra/backend/app/main.py",
    "DEBUG = True",
    "DEBUG = False"
)

# 2. Commit
client.git_commit("Fix: disable debug mode")

# 3. Push
client.git_push()

# 4. Deploy
client.docker_down()
client.docker_build()
client.docker_up()

# 5. Health check
health = client.health_check()

# 6. Status
ps = client.docker_ps()

client.disconnect()
print(f"Deploy completo! Status: {ps}")
```

---

## 🛠️ MANUAL DO USO DIRETO

Se preferir usar sem mensagens:

```bash
# Terminal
cd C:\Users\benja\Desktop\eureka-terra
python vps_client.py

# Menu aparece, escolha opção (1-9)
# Opção 1 = Deploy Completo
```

---

## ⚠️ CUIDADOS

1. **Sem confirmação manual:** Uma vez executado, C vai fazer sem pedir segundo aviso
2. **Timeouts:** Comandos que demoram >300s podem falhar
3. **Passwords em código:** Não está seguro para ambientes públicos
4. **SSH Key Authentication:** Futuramente, usar chaves em vez de senha

---

## 🚀 PRÓXIMOS PASSOS

1. **Teste local:** `python claude_vps_automation.py`
2. **Diga ao Claude:** "Faça deploy na VPS"
3. **Claude executa automaticamente** ✓

---

## 📞 SUPORTE

Se algo falhar:
```
Claude, mostra os logs dos últimos 100 linhas do backend
```

Claude vai retornar os logs e você vê o erro.

---

**Agora Claude pode trabalhar na VPS sem sua interferência!** 🎉
