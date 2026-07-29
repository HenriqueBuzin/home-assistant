# Reconstrução do projeto

Este repositório descreve toda a infraestrutura multi-site do Home Assistant.

## Contrato

- Home Assistant está fixado em 2026.7.4 e é o único serviço, chamado `backend`.
- O backend atende na porta interna 8123 e participa diretamente da rede externa `proxy-network`.
- `init.sh` cria `/config/configuration.yaml` apenas quando ele ainda não existe, habilitando proxy confiável e a URL externa.
- Dados persistentes ficam em `HA_CONFIG_ROOT`, fora do checkout.

## Compose

- `docker-compose.yml`: dev, projeto `home-assistant-${HA_SITE}-dev`, imagem terminada em `-dev`.
- `docker-compose-prod.yml`: produção, projeto `home-assistant-${HA_SITE}`, sem sufixo `-prod`.
- Serviço em ambos: `backend`.
- São proibidos `version`, profiles, Caddy, Nginx, PostgreSQL e Redis dentro do projeto.
- Comandos de inicialização ficam no Dockerfile/entrypoint, nunca no Compose.

O serviço tem alias `home-assistant-<site>[-dev]`, labels de projeto/ambiente/site/versão, rotação de logs, healthcheck, restart e `no-new-privileges`. O proxy reverso externo encaminha para esse alias na porta 8123 com WebSocket habilitado.

## Branches e deploy

- `fln`: `HA_SITE=fln`, produção.
- `cxs`: `HA_SITE=cxs`, produção.
- `fln-dev`: `HA_SITE=fln`, desenvolvimento.
- `cxs-dev`: `HA_SITE=cxs`, desenvolvimento.
- `main`: não faz deploy; mantém a fonte comum.

Arquivos de ambiente ficam em `/root/projects/envs/home-assistant-<site>[-dev].env` e são ligados simbolicamente como `.env`. O diretório de deploy segue o mesmo nome do projeto Compose.

## Variáveis

Obrigatórias: `HA_SITE`, `HA_URL`, `HA_CONFIG_ROOT`. Opcional: `IMAGE_TAG`.

## Qualidade

GitHub Actions e Jenkins usam as etapas `Install`, `Verify`, `Compose`, `Container` e `Deploy`. `scripts/verify.sh` valida shell, contratos e os dois Compose. O E2E tenta a plataforma externa e usa Playwright contra `E2E_BASE_URL` quando necessário.

## Reconstrução

Para recriar o serviço, gere os dois Compose com os contratos acima, o Dockerfile baseado na versão fixada do Home Assistant, o `init.sh`, os pipelines e os testes. Crie `proxy-network`, o diretório persistente e o `.env` externo antes de subir o ambiente.
