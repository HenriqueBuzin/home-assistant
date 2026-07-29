# Home Assistant

Infraestrutura padronizada para quatro instalações independentes do Home Assistant:

| Branch | Ambiente | Projeto Compose | Arquivo Compose | Alias na rede |
| --- | --- | --- | --- | --- |
| `cxs` | Produção Caxias | `home-assistant-cxs` | `docker-compose-prod.yml` | `home-assistant-cxs` |
| `cxs-dev` | Desenvolvimento Caxias | `home-assistant-cxs-dev` | `docker-compose.yml` | `home-assistant-cxs-dev` |
| `fln` | Produção Florianópolis | `home-assistant-fln` | `docker-compose-prod.yml` | `home-assistant-fln` |
| `fln-dev` | Desenvolvimento Florianópolis | `home-assistant-fln-dev` | `docker-compose.yml` | `home-assistant-fln-dev` |

A branch `main` mantém a fonte comum alinhada, mas não faz deploy pelo Jenkins.

## Como funciona

- Cada ambiente executa um único serviço Compose chamado `backend`.
- O Home Assistant atende internamente na porta `8123`.
- O Nginx Proxy Manager é externo a este repositório e acessa o alias do ambiente pela rede Docker externa `proxy-network`.
- O proxy deve encaminhar para `http://<alias>:8123` com suporte a WebSocket habilitado.
- Não há Caddy, Nginx, PostgreSQL ou Redis dentro deste projeto.
- Produção e desenvolvimento possuem configurações, backups, containers e projetos Compose separados.

## Arquivos de ambiente

Os arquivos reais ficam fora do Git:

- `/root/projects/envs/home-assistant-cxs.env`
- `/root/projects/envs/home-assistant-cxs-dev.env`
- `/root/projects/envs/home-assistant-fln.env`
- `/root/projects/envs/home-assistant-fln-dev.env`

O Jenkins cria um link simbólico chamado `.env` no diretório de cada projeto. Cada arquivo define:

- `HA_SITE`: `cxs` ou `fln`;
- `HA_URL`: URL pública completa do ambiente;
- `HA_CONFIG_ROOT`: pasta persistente `config/` daquele ambiente;
- `IMAGE_TAG`: tag opcional da imagem.

Exemplo de caminho persistente de produção: `/root/projects/volumes/home-assistant-cxs/config`.

## Persistência e backups

Cada ambiente possui seu próprio volume:

- `/root/projects/volumes/home-assistant-cxs`
- `/root/projects/volumes/home-assistant-cxs-dev`
- `/root/projects/volumes/home-assistant-fln`
- `/root/projects/volumes/home-assistant-fln-dev`

Dentro de cada volume:

- `config/` contém a configuração ativa e deve sobreviver a todos os deployments;
- `restore/` mantém o arquivo `.tar`, `.tar.gz` ou `.tgz` correspondente ao ambiente.

O backup em `restore/` pode permanecer guardado permanentemente. Ele só é restaurado quando `config/` está completamente vazio. Uma configuração existente nunca é substituída.

O restaurador aceita:

- um arquivo tar que contenha diretamente a configuração;
- um backup oficial descriptografado que contenha `homeassistant.tar` ou `homeassistant.tar.gz`.

Backups criptografados, inseguros, inválidos ou ambíguos interrompem a inicialização com erro. Deve existir no máximo um arquivo de backup suportado em cada pasta `restore/`.

## Recriação intencional

Use este procedimento somente quando for necessário voltar ao onboarding ou restaurar o ambiente do zero:

1. Pare o Compose do ambiente correto.
2. Mova o conteúdo atual de `config/` para uma pasta de segurança com nome `config-onboarding-<data-hora>`.
3. Recrie `config/` vazio.
4. Preserve o arquivo tar dentro de `restore/`.
5. Execute novamente o Jenkins da branch correspondente.
6. Confirme o site, as integrações e a persistência.
7. Remova as pastas `config-onboarding-*` somente depois da validação.

Um deployment normal não pode exigir esse processo. Se o onboarding reaparecer após uma alteração comum, existe uma falha de persistência, caminho ou ambiente que deve ser investigada antes de apagar qualquer dado.

## Deploy

O pipeline possui as mesmas etapas em todas as branches implantáveis:

1. `Install`
2. `Verify`
3. `Compose`
4. `Container`
5. `Deploy`

O Jenkins copia o checkout para `/root/projects/home-assistant-<site>[-dev]`, liga o `.env` externo, valida o caminho persistente, constrói a imagem, recria o container e espera o healthcheck. A pasta `config/` não é removida durante o deploy.

## Validação local

Pré-requisitos: Docker com Compose, Node.js e npm nas versões declaradas em `package.json`.

```bash
cp .env.example .env
docker network inspect proxy-network >/dev/null 2>&1 || docker network create proxy-network
npm ci
sh scripts/verify.sh
npm run test:e2e:list
```

O teste E2E usa a plataforma configurada em `E2E_PLATFORM_COMMAND`. Se ela não estiver disponível ou falhar, Playwright é o adaptador de fallback.

## Diagnóstico rápido

- `502 Bad Gateway`: confira se o proxy aponta para o alias correto na porta `8123`, está na `proxy-network` e possui WebSocket habilitado.
- Tela de onboarding inesperada: confira `HA_CONFIG_ROOT`, o bind mount e o conteúdo de `config/`; não limpe o volume antes de identificar a causa.
- Restauração ignorada: `config/` já contém algum arquivo.
- Container não inicia ao restaurar: confira se há exatamente um backup suportado e descriptografado em `restore/`.
- Ambiente errado: confira a correspondência entre branch, `HA_SITE`, arquivo `.env`, diretório de projeto e volume.

O contrato técnico completo para manutenção ou reconstrução está em [AGENTS.md](AGENTS.md).
