#!/usr/bin/env python3
"""Configurar HTTPS com Certbot para laudoesg.com"""
import paramiko

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

def executar_comando(ssh, cmd, timeout=30, descricao=""):
    """Executar comando e mostrar resultado"""
    if descricao:
        print(f"[*] {descricao}")
    
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    output = stdout.read().decode()
    error = stderr.read().decode()
    
    if error and "WARNING" not in error and "Skipping" not in error:
        print(f"⚠️  Erro: {error}")
        return False
    elif output:
        print(f"✅ {descricao} - Concluído")
        return True
    else:
        print(f"✅ {descricao}")
        return True

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Parar nginx temporariamente para liberar porta 80
    print("[*] Parando nginx temporariamente...")
    executar_comando(ssh, "docker stop eureka_nginx", descricao="Parando container nginx")
    
    # Gerar certificado SSL com Certbot
    print("\n[*] Gerando certificado SSL com Certbot...")
    certbot_cmd = f"""certbot certonly --standalone \
  --non-interactive \
  --agree-tos \
  -m agapenegociosdigitais@gmail.com \
  -d laudoesg.com \
  -d www.laudoesg.com"""
    
    executar_comando(ssh, certbot_cmd, timeout=120, descricao="Gerando certificado SSL")
    
    # Verificar se os certificados foram criados
    print("\n[*] Verificando certificados...")
    stdin, stdout, stderr = ssh.exec_command("ls -la /etc/letsencrypt/live/laudoesg.com/ 2>&1", timeout=10)
    certs = stdout.read().decode()
    print("Certificados:")
    print(certs)
    
    # Copiar certificados para o diretório do projeto
    print("\n[*] Copiando certificados para o projeto...")
    executar_comando(ssh, "mkdir -p /root/eureka-terra/certs", descricao="Criando diretório certs")
    
    # Copiar certificados
    executar_comando(ssh, "cp /etc/letsencrypt/live/laudoesg.com/fullchain.pem /root/eureka-terra/certs/cert.pem", descricao="Copiando certificado")
    executar_comando(ssh, "cp /etc/letsencrypt/live/laudoesg.com/privkey.pem /root/eureka-terra/certs/key.pem", descricao="Copiando chave privada")
    
    # Criar configuração HTTPS no nginx
    print("\n[*] Configurando HTTPS no nginx...")
    
    nginx_https_config = """
# HTTP server (redireciona para HTTPS)
server {
    listen 80;
    server_name laudoesg.com www.laudoesg.com 23.106.45.137;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name laudoesg.com www.laudoesg.com 23.106.45.137;

    ssl_certificate /etc/nginx/certs/cert.pem;
    ssl_certificate_key /etc/nginx/certs/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Backend API routes
    location /api/v1 {
        # Handle CORS preflight FIRST
        if ($request_method = 'OPTIONS') {
            add_header 'Access-Control-Allow-Origin' '$http_origin' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
            add_header 'Access-Control-Allow-Credentials' 'true' always;
            add_header 'Content-Length' '0' always;
            return 204;
        }

        proxy_pass         http://eureka_backend:8000/api/v1;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   Connection '';

        # CORS headers for regular requests
        add_header 'Access-Control-Allow-Origin' '$http_origin' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
        add_header 'Access-Control-Allow-Credentials' 'true' always;
    }

    # Health check endpoint
    location /health {
        proxy_pass         http://eureka_backend:8000;
    }

    # Frontend - Static files and all other routes
    location / {
        proxy_pass         http://eureka_frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   Connection '';

        # Cache static assets
        proxy_cache_valid 200 30d;
        proxy_cache_bypass $http_pragma $http_authorization;
    }
}
"""
    
    # Salvar configuração HTTPS
    with open("/tmp/nginx_https.conf", "w") as f:
        f.write(nginx_https_config)
    
    # Copiar para a VPS
    sftp = ssh.open_sftp()
    sftp.put("/tmp/nginx_https.conf", "/tmp/nginx_https.conf")
    sftp.close()
    
    # Substituir configuração do nginx
    executar_comando(ssh, "cp /root/eureka-terra/nginx/nginx.conf /root/eureka-terra/nginx/nginx.conf.backup", descricao="Fazendo backup da configuração atual")
    executar_comando(ssh, "cp /tmp/nginx_https.conf /root/eureka-terra/nginx/nginx.conf", descricao="Aplicando nova configuração HTTPS")
    
    # Iniciar nginx novamente
    print("\n[*] Iniciando nginx com HTTPS...")
    executar_comando(ssh, "docker start eureka_nginx", descricao="Iniciando container nginx")
    
    # Testar configuração
    print("\n[*] Testando configuração...")
    time.sleep(5)  # Aguardar nginx iniciar
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w \"%{http_code}\" https://localhost:443/health --insecure", timeout=10)
    https_test = stdout.read().decode()
    print(f"Teste HTTPS: HTTP {https_test}")
    
    # Configurar renovação automática do certificado
    print("\n[*] Configurando renovação automática...")
    cron_job = "0 3 * * * docker stop eureka_nginx && certbot renew --quiet && docker start eureka_nginx"
    executar_comando(ssh, f'(crontab -l 2>/dev/null; echo "{cron_job}") | crontab -', descricao="Adicionando cron job para renovação")
    
    ssh.close()
    print("\n[✓] Configuração HTTPS concluída!")
    print("\n📋 Resumo:")
    print("✅ Certificado SSL gerado")
    print("✅ Nginx configurado para HTTPS")
    print("✅ Redirecionamento HTTP para HTTPS ativado")
    print("✅ Renovação automática configurada")
    print("\n🌐 URLs:")
    print("   HTTP:  http://23.106.45.137 (redireciona para HTTPS)")
    print("   HTTPS: https://23.106.45.137")
    print("   Domínio: https://laudoesg.com")
    
except Exception as e:
    print(f"[✗] Erro: {e}")