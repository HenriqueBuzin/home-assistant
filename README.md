# Home Assistant

Infraestrutura multi-site para Home Assistant 2026.7.4 publicado diretamente pelo proxy reverso externo.

## Branches

- `fln` e `cxs`: produção com `docker-compose-prod.yml`.
- `fln-dev` e `cxs-dev`: desenvolvimento com `docker-compose.yml`.
- `main`: fonte comum, validação e integração.

Cada ambiente recebe por `.env` externo o site, a URL pública e o diretório persistente. Jenkins cria o link simbólico; nenhum dado ou segredo fica no Git.

## Restauração inicial

Cada ambiente possui uma pasta própria em `/root/projects/volumes/home-assistant-<site>[-dev]/restore`. Para iniciar um ambiente vazio a partir de backup:

1. deixe `config/` vazio;
2. coloque exatamente um arquivo `.tar`, `.tar.gz` ou `.tgz` em `restore/`;
3. execute o deploy da branch correspondente.

O bootstrap aceita um tar direto da configuração ou um backup oficial descriptografado que contenha `homeassistant.tar[.gz]`. Configuração existente nunca é sobrescrita. Backup ausente inicia uma instalação nova; arquivo inválido, criptografado ou múltiplos backups interrompem o container com erro explícito.

## Serviços

- `backend`: Home Assistant, conectado à `proxy-network` com alias por ambiente e porta interna `8123`.

O Nginx Proxy Manager externo encaminha HTTP para o alias do ambiente na porta `8123`, com WebSocket habilitado. Não há Caddy, profiles, banco de dados ou Redis no projeto.

## Validação

```bash
cp .env.example .env
docker network inspect proxy-network >/dev/null 2>&1 || docker network create proxy-network
npm ci
sh scripts/verify.sh
npm run test:e2e:list
```

O adaptador E2E usa `E2E_PLATFORM_COMMAND` primeiro e Playwright como fallback. Consulte `AGENTS.md` para o contrato completo de reconstrução.
