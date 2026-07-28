# Home Assistant

Infraestrutura multi-site para Home Assistant 2026.7.4 atrás de Caddy 2.11.4.

## Branches

- `fln` e `cxs`: produção com `docker-compose-prod.yml`.
- `fln-dev` e `cxs-dev`: desenvolvimento com `docker-compose.yml`.
- `main`: fonte comum, validação e integração.

Cada ambiente recebe por `.env` externo o site, a URL pública e o diretório persistente. Jenkins cria o link simbólico; nenhum dado ou segredo fica no Git.

## Serviços

- `backend`: Home Assistant.
- `web`: Caddy, conectado à `proxy-network`.

Não há Nginx, profiles, banco de dados ou Redis no projeto.

## Validação

```bash
cp .env.example .env
docker network inspect proxy-network >/dev/null 2>&1 || docker network create proxy-network
npm ci
sh scripts/verify.sh
npm run test:e2e:list
```

O adaptador E2E usa `E2E_PLATFORM_COMMAND` primeiro e Playwright como fallback. Consulte `AGENTS.md` para o contrato completo de reconstrução.
