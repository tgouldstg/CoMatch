# Internet Deployment (Recommended)

Recommended approach: run the app in Docker and put it behind Cloudflare Tunnel (no open inbound ports on your host).

## 1) Prepare secrets

Create `.env` from `.env.example` and set strong values:

```bash
cp .env.example .env
```

## 2) Build + run locally

```bash
docker build -t company-match-api:local .
docker run -d --name company-match-api \
  --env-file .env \
  -p 127.0.0.1:8000:8000 \
  --restart unless-stopped \
  company-match-api:local
```

App listens on localhost only (not public).

## 3) Expose via Cloudflare Tunnel

Install `cloudflared`, then:

```bash
cloudflared tunnel login
cloudflared tunnel create company-match-api
cloudflared tunnel route dns company-match-api match.yourdomain.com
```

Create config (e.g. `~/.cloudflared/config.yml`):

```yaml
tunnel: company-match-api
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: match.yourdomain.com
    service: http://127.0.0.1:8000
  - service: http_status:404
```

Run tunnel:

```bash
cloudflared tunnel run company-match-api
```

Now your app is reachable at `https://match.yourdomain.com` with TLS, without opening server ports publicly.

## 4) Hardening checklist

- Use very strong `APP_AUTH_PASSWORD` and `APP_AUTH_SECRET`
- Enable Cloudflare WAF + bot protections
- Add Cloudflare Access (optional second login layer)
- Restrict CORS in app if needed
- Add rate limiting (next enhancement)
- Keep Docker image and host patched
