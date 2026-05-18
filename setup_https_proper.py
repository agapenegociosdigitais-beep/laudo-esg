#!/usr/bin/env python3
"""Configurar HTTPS corretamente no nginx"""
import paramiko

HOST = "23.106.45.137"
USER = "root"
PASSWORD = "JVghqGUersYW6h8Q"

print(f"[*] Conectando em {USER}@{HOST}...")

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    
    print("[✓] Conectado!\n")
    
    # Ler configuração atual
    print("[*] Lendo configuração atual do nginx...")
    stdin, stdout, stderr = ssh.exec_command("cat /root/eureka-terra/nginx/nginx.conf", timeout=10)
    current_config = stdout.read().decode()
    
    # Configuração HTTPS completa e correta
    https_config = """events {
    worker_connections 1024;
}

http {
    # Configurações gerais
    sendfile        on;
    tcp_nopush      on;
    tcp_nodelay     on;
    keepalive_timeout 65;
    client_max_body_size 20M;

    # Logs
    access_log /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log;

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
}
"""
    
    # Salvar nova configuração
    print("[*] Salvando nova configuração HTTPS...")
    with open("/tmp/nginx_https_proper.conf", "w") as f:
        f.write(https_config)
    
    # Copiar para a VPS
    sftp = ssh.open_sftp()
    sftp.put("/tmp/nginx_https_proper.conf", "/tmp/nginx_https_proper.conf")
    sftp.close()
    
    # Fazer backup e aplicar nova configuração
    print("[*] Aplicando nova configuração...")
    stdin, stdout, stderr = ssh.exec_command("cp /root/eureka-terra/nginx/nginx.conf /root/eureka-terra/nginx/nginx.conf.backup2", timeout=10)
    print("✅ Backup criado")
    
    stdin, stdout, stderr = ssh.exec_command("cp /tmp/nginx_https_proper.conf /root/eureka-terra/nginx/nginx.conf", timeout=10)
    print("✅ Nova configuração aplicada")
    
    # Reiniciar nginx
    print("\n[*] Reiniciando nginx...")
    stdin, stdout, stderr = ssh.exec_command("docker restart eureka_nginx", timeout=30)
    print("✅ Nginx reiniciado")
    
    # Aguardar e testar
    print("\n[*] Aguardando e testando...")
    import time
    time.sleep(5)
    
    stdin, stdout, stderr = ssh.exec_command("docker ps --filter name=eureka_nginx --format '{{.Status}}'", timeout=10)
    status = stdout.read().decode().strip()
    print(f"Status: {status}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:80/health", timeout=10)
    http_test = stdout.read().decode()
    print(f"Teste HTTP: {http_test}")
    
    stdin, stdout, stderr = ssh.exec_command("curl -s -o /dev/null -w '%{http_code}' https://localhost:443/health --insecure", timeout=10)
    https_test = stdout.read().decode()
    print(f"Teste HTTPS: {https_test}")
    
    ssh.close()
    print("\n[✓] Configuração HTTPS concluída!")
    
except Exception as e:
    print(f"[✗] Erro: {e}")