# Publicar o app no subdomínio (Hostinger VPS)

Meta: rodar o app em **https://esmaltes.nghair.com.br** e apontar o link
"Administração" do site para esse endereço. O site `nghair.com.br` continua
intacto.

---

## Passo 1 — DNS (igual nos dois casos)

No painel da Hostinger (ou onde fica o DNS do domínio `nghair.com.br`), crie um
registro apontando o subdomínio para o IP do seu VPS:

```
Tipo: A
Nome: esmaltes
Valor: <IP do seu VPS>
TTL: padrão
```

Aguarde alguns minutos para propagar. Teste: `ping esmaltes.nghair.com.br`
deve responder com o IP do VPS.

---

## Caso A — VPS com painel (Coolify / Dokploy)

Se o seu "deploy automático a cada commit" é feito por um painel (a Hostinger
oferece templates de **Coolify** e **Dokploy**), é o mais fácil:

1. No projeto do app (que aponta para o repositório `ControleEsmaltes`):
   - **Build:** detecta o `Dockerfile` automaticamente (ou use Nixpacks).
   - **Porta:** `8000`.
   - **Domínio:** defina `esmaltes.nghair.com.br` (o painel cuida do proxy
     reverso e do certificado HTTPS automaticamente).
2. **Volume persistente:** monte um volume na pasta `/app/data` para preservar
   o banco e as fotos entre deploys.
3. **Variáveis de ambiente** (recomendado, para proteger o painel com senha):
   ```
   ADMIN_USER=seu_usuario
   ADMIN_PASS=sua_senha_forte
   ```
4. Faça o deploy. Abra `https://esmaltes.nghair.com.br` para conferir.

---

## Caso B — VPS Linux puro (Nginx)

### 1. Subir o app (via Docker — recomendado)

```bash
cd /opt
git clone <url-do-repo-ControleEsmaltes> ControleEsmaltes
cd ControleEsmaltes
docker build -t esmaltes .
docker run -d --name esmaltes \
  -p 127.0.0.1:8000:8000 \
  -v /opt/esmaltes-data:/app/data \
  -e ADMIN_USER=seu_usuario \
  -e ADMIN_PASS=sua_senha_forte \
  --restart unless-stopped \
  esmaltes
```

> Alternativa sem Docker: crie um virtualenv, `pip install -r requirements.txt`
> e rode via `systemd` com
> `uvicorn app.main:app --host 127.0.0.1 --port 8000`.

### 2. Nginx (proxy reverso para o subdomínio)

Crie `/etc/nginx/sites-available/esmaltes.nghair.com.br`:

```nginx
server {
    listen 80;
    server_name esmaltes.nghair.com.br;

    # As fotos podem ser grandes — libere o tamanho do upload
    client_max_body_size 25M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Ative e recarregue:

```bash
ln -s /etc/nginx/sites-available/esmaltes.nghair.com.br /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

### 3. HTTPS (Let's Encrypt)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d esmaltes.nghair.com.br
```

Abra `https://esmaltes.nghair.com.br` para conferir.

---

## Passo 2 — Corrigir o link no site

No repositório do site (`NGHair-landigpage`), troque o `href` do item
"Administração" (no menu desktop **e** no mobile):

```diff
- href="https://www.nghair.com.br/controleEsmaltes"
+ href="https://esmaltes.nghair.com.br"
```

Veja o prompt pronto para essa edição em `INTEGRACAO-SITE.md`.
