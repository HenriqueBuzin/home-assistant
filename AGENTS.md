# Especificação de reconstrução

Este documento é a fonte técnica canônica do repositório. Ele deve permitir que um agente recrie a aplicação e sua infraestrutura do zero sem consultar a implementação anterior. Não copie código histórico: implemente novamente o comportamento descrito aqui, usando versões LTS atuais e dependências estáveis compatíveis, salvo quando uma versão estiver explicitamente fixada neste contrato.

## Objetivo

Construir uma infraestrutura Docker multiambiente para quatro instalações independentes do Home Assistant, com deploy pelo Jenkins, validação pelo GitHub Actions, persistência fora do checkout, restauração automática segura de backup e publicação por um proxy reverso externo.

O repositório não desenvolve o Home Assistant. Ele empacota a imagem oficial, adiciona bootstrap e restauração, padroniza Compose, testes e entrega contínua.

## Resultado obrigatório

A reconstrução deve produzir:

- uma branch comum `main`, sem deploy;
- branches implantáveis `cxs`, `cxs-dev`, `fln` e `fln-dev`;
- um Compose de desenvolvimento chamado `docker-compose.yml`;
- um Compose de produção chamado `docker-compose-prod.yml`;
- um único serviço Compose chamado `backend`;
- uma imagem Docker de runtime baseada na imagem oficial estável do Home Assistant;
- um entrypoint responsável pelo bootstrap;
- um restaurador de backups escrito em Python da biblioteca padrão;
- testes unitários do restaurador;
- verificação estática dos contratos de infraestrutura;
- teste E2E com plataforma externa e Playwright como fallback;
- pipelines equivalentes no Jenkins e no GitHub Actions;
- somente `README.md` e `AGENTS.md` como documentação Markdown canônica.

## Matriz de ambientes

| Branch | Site | Tipo | Projeto e diretório | Ambiente externo | Volume raiz | Alias |
| --- | --- | --- | --- | --- | --- | --- |
| `cxs` | `cxs` | produção | `home-assistant-cxs` | `home-assistant-cxs.env` | `home-assistant-cxs` | `home-assistant-cxs` |
| `cxs-dev` | `cxs` | desenvolvimento | `home-assistant-cxs-dev` | `home-assistant-cxs-dev.env` | `home-assistant-cxs-dev` | `home-assistant-cxs-dev` |
| `fln` | `fln` | produção | `home-assistant-fln` | `home-assistant-fln.env` | `home-assistant-fln` | `home-assistant-fln` |
| `fln-dev` | `fln` | desenvolvimento | `home-assistant-fln-dev` | `home-assistant-fln-dev.env` | `home-assistant-fln-dev` | `home-assistant-fln-dev` |

`main` deve permanecer alinhada com a fonte compartilhada, mas o Jenkins precisa ignorá-la. O filtro do multibranch job também deve excluir `main`; a proteção no próprio Jenkinsfile continua obrigatória.

## Topologia

Há exatamente um container por ambiente. Seu serviço lógico se chama `backend` e executa o Home Assistant na porta interna `8123`.

Todos os containers participam diretamente da rede Docker externa `proxy-network`. Cada container recebe exclusivamente o alias indicado na matriz. O Nginx Proxy Manager existente na VPS participa da mesma rede e encaminha cada domínio para o alias correspondente na porta `8123`, usando HTTP e WebSocket.

Não adicionar proxy reverso ao repositório. Não adicionar Caddy, Nginx, banco de dados, Redis, profiles ou o campo legado `version` aos arquivos Compose. Não publicar porta no host quando o acesso pela rede externa for suficiente.

## Compose

Os dois arquivos Compose devem possuir a mesma estrutura e diferir apenas pelo ambiente:

- `docker-compose.yml` representa desenvolvimento, usa projeto e alias com sufixo `-dev` e imagem com tag de desenvolvimento;
- `docker-compose-prod.yml` representa produção, usa projeto e alias sem `-prod` e imagem de produção;
- o nome do projeto deve ser declarado pelo próprio Compose e também exportado pelo pipeline;
- o serviço deve se chamar `backend`;
- comandos de inicialização pertencem ao Dockerfile ou entrypoint, nunca ao Compose;
- o bind de configuração usa `HA_CONFIG_ROOT` como origem e `/config` como destino;
- a pasta `restore/` específica do projeto é montada como somente leitura em `/restore`;
- o horário do host é montado como somente leitura e o timezone é `America/Sao_Paulo`;
- a porta `8123` é apenas exposta à rede Docker;
- devem existir restart automático, healthcheck HTTP, rotação de logs, labels padronizadas e `no-new-privileges`;
- a rede `proxy-network` deve ser marcada como externa.

As labels devem identificar ao menos projeto, ambiente, site e versão da imagem. A rotação de logs deve impedir crescimento ilimitado. O healthcheck deve consultar o Home Assistant localmente e tolerar o tempo maior de sua primeira inicialização.

## Imagem e bootstrap

Use uma construção multi-stage:

- o estágio de verificação usa a versão LTS de Node.js declarada no projeto, instala pelo lockfile e confirma que a suíte E2E pode ser descoberta;
- o estágio final usa a versão oficial estável do Home Assistant definida para todos os ambientes;
- scripts necessários são copiados com permissão de execução;
- os testes unitários do restaurador são executados durante o build;
- o entrypoint personalizado termina entregando o processo ao entrypoint oficial do Home Assistant, preservando sinais e encerramento correto.

Na primeira inicialização sem backup, o bootstrap deve criar uma configuração mínima somente se `configuration.yaml` ainda não existir. Ela precisa habilitar configuração padrão, temas, URL externa recebida pelo ambiente, URL interna local, cabeçalhos de proxy e redes privadas confiáveis necessárias ao proxy Docker.

O bootstrap nunca deve substituir uma configuração válida.

## Persistência

Todos os dados mutáveis ficam fora do checkout em `/root/projects/volumes`.

Cada um dos quatro ambientes possui um volume raiz independente com:

- `config/`, montado como leitura e escrita em `/config`;
- `restore/`, montado como somente leitura em `/restore`.

Produção e desenvolvimento nunca compartilham `config/`. Um deployment normal pode recriar imagem e container, mas deve preservar integralmente o bind mount. O pipeline pode criar as pastas ausentes, porém nunca pode apagar, esvaziar, substituir ou mudar silenciosamente o caminho de `config/`.

Os arquivos tar de restauração permanecem em `restore/` para uso futuro. Sua presença não dispara restauração se `config/` contiver qualquer item.

## Restauração automática

Antes de gerar a configuração mínima, o entrypoint executa o restaurador.

O restaurador deve:

- aceitar os diretórios de restore e configuração como argumentos;
- criar os diretórios quando ausentes;
- encerrar com sucesso e não alterar nada quando `config/` não estiver vazio;
- encerrar com sucesso e permitir instalação nova quando não houver backup;
- aceitar exatamente um arquivo `.tar`, `.tar.gz` ou `.tgz`;
- rejeitar mais de um backup elegível;
- aceitar um tar direto contendo `configuration.yaml` ou `.storage`;
- aceitar backup oficial descriptografado contendo exatamente um `homeassistant.tar` ou `homeassistant.tar.gz`;
- localizar a raiz real da configuração sem depender de um prefixo fixo;
- extrair primeiro para uma pasta temporária e copiar para `config/` somente após validação completa;
- rejeitar caminhos absolutos, travessia por `..`, links simbólicos, hard links, dispositivos e raízes ambíguas;
- rejeitar backup sem `configuration.yaml` e sem `.storage`;
- explicar que um arquivo ilegível pode estar criptografado e deve ser baixado descriptografado;
- nunca remover nem modificar o arquivo original em `restore/`;
- nunca sobrescrever uma configuração existente.

A suíte unitária deve cobrir no mínimo restauração direta, backup oficial aninhado, preservação de configuração existente, múltiplos backups e path traversal. Novos casos de segurança descobertos devem ganhar teste de regressão.

## Recriação e recuperação operacional

Voltar ao onboarding é uma ação deliberada, não parte do deploy:

1. parar o Compose do ambiente correto;
2. mover a configuração existente para `config-onboarding-<data-hora>` dentro do volume daquele ambiente;
3. recriar `config/` vazio;
4. manter exatamente o tar correspondente em `restore/`;
5. executar o Jenkins da branch correspondente;
6. validar acesso, integrações e persistência;
7. apagar `config-onboarding-*` apenas após confirmação.

Se um deploy normal apresentar onboarding, classificar como defeito de persistência. Verificar o valor real de `HA_CONFIG_ROOT`, o link `.env`, o bind resolvido pelo Compose, o diretório do projeto e o conteúdo do volume antes de qualquer limpeza.

## Variáveis e arquivos externos

O Git contém apenas `.env.example`, sem segredos ou dados reais.

Variáveis:

- `HA_SITE`, obrigatória, aceita `cxs` ou `fln`;
- `HA_URL`, obrigatória, contém a URL pública completa do ambiente;
- `HA_CONFIG_ROOT`, obrigatória, aponta exatamente para `/root/projects/volumes/<projeto>/config`;
- `IMAGE_TAG`, opcional, identifica a imagem e usa valor local previsível quando ausente.

Na VPS, os arquivos ficam em `/root/projects/envs/<projeto>.env`. Jenkins cria um link simbólico `.env` no diretório `/root/projects/<projeto>`. Não copiar o conteúdo do arquivo externo para o Git e não criar uma hierarquia paralela de segredos.

## Jenkins

As branches implantáveis executam, nesta ordem, as etapas `Install`, `Verify`, `Compose`, `Container` e `Deploy`.

Responsabilidades:

- `Install`: confirmar Docker Compose e registrar que dependências Node são instaladas no build;
- `Verify`: executar a verificação do repositório e construir o estágio de validação da imagem;
- `Compose`: derivar site e ambiente exclusivamente da branch, criar o diretório do projeto, copiar o checkout sem tocar nos volumes, ligar o `.env`, validar `HA_CONFIG_ROOT`, garantir `config/` e `restore/` e validar o Compose;
- `Container`: construir com atualização da imagem-base;
- `Deploy`: garantir a rede externa, encerrar somente o projeto correto, subir com remoção de órfãos, aguardar healthcheck, testar HTTP pelo alias na rede e exibir o estado final.

Execuções concorrentes do mesmo job devem ser bloqueadas. Logs devem ter timestamps. Falhas de subida ou healthcheck devem imprimir logs recentes do `backend`. O deploy nunca usa `rsync` nem remove o volume persistente.

O Jenkinsfile precisa ter condições explícitas para as quatro branches, mesmo que o multibranch job já possua filtro. Assim, uma descoberta acidental de `main` não executa etapas de deploy.

## GitHub Actions

O workflow deve ser acionado em todas as branches relevantes e executar os mesmos gates técnicos do Jenkins, exceto o deploy na VPS. Deve:

- fazer checkout;
- configurar a versão exata de Node.js e cache do npm;
- instalar pelo lockfile;
- executar verificações, testes unitários e descoberta E2E;
- criar um `.env` de CI ou fornecer variáveis equivalentes antes de validar Compose;
- validar ambos os arquivos Compose;
- construir os estágios da imagem;
- gerar SBOM e relatórios completos do container;
- comparar o scan da imagem construída com o scan do mesmo digest oficial usado como base;
- bloquear vulnerabilidades altas ou críticas introduzidas pela camada deste repositório.

O workflow não pode depender dos arquivos `.env` privados da VPS.

A imagem oficial pode conter vulnerabilidades corrigíveis em binários e dependências que este projeto não controla. Esses achados herdados devem permanecer visíveis no relatório, mas não podem tornar o pipeline permanentemente impossível de executar. Não criar exceções genéricas: o gate compara identificador da vulnerabilidade, pacote e tipo entre a base e a imagem final, falhando somente para achados altos ou críticos novos. A atualização para uma nova imagem oficial deve renovar naturalmente essa linha de base.

## Testes e qualidade

A reconstrução deve incluir:

- testes unitários do restaurador Python;
- testes unitários do comparador de baseline de vulnerabilidades;
- verificação de sintaxe do shell;
- validação dos dois arquivos Compose;
- asserts que impeçam `version`, profiles, Caddy e Nginx internos;
- asserts dos nomes de serviço, projeto, aliases, porta e caminhos de restore;
- smoke test HTTP do container;
- regressão para todos os bugs de restauração e persistência conhecidos;
- E2E por plataforma externa configurável;
- fallback E2E por Playwright.

O comando E2E deve tentar primeiro `E2E_PLATFORM_COMMAND`. Se a plataforma retornar sucesso, o gate termina com sucesso. Se estiver ausente ou falhar, deve executar Playwright e propagar corretamente o status final.

As versões de Node.js, npm, TypeScript e Playwright devem estar fixadas e coerentes entre `package.json`, lockfile, Dockerfile, CI e arquivos auxiliares. O projeto deve bloquear versões incompatíveis por `engines` e configuração do npm.

## Arquivos esperados

A implementação reconstruída deve conter ao menos:

- `.github/workflows/ci.yml`;
- `.dockerignore`;
- `.env.example`;
- `.gitattributes`;
- `.gitignore`;
- `.npmrc`;
- `.nvmrc`;
- `AGENTS.md`;
- `README.md`;
- `Dockerfile`;
- `Jenkinsfile`;
- `docker-compose.yml`;
- `docker-compose-prod.yml`;
- `init.sh`;
- `package.json`;
- lockfile do npm;
- configuração e cenários Playwright;
- restaurador Python e seus testes;
- comparador de baseline dos relatórios Grype;
- script de verificação;
- adaptador E2E.

Não criar documentação Markdown adicional. Informações humanas pertencem ao `README.md`; decisões, contratos e instruções completas para agentes pertencem a este arquivo.

## Critérios de aceitação

A reconstrução está pronta somente quando:

- os quatro ambientes são isolados e os nomes correspondem exatamente à matriz;
- produção não possui sufixo `-prod` e desenvolvimento possui `-dev`;
- os dois Compose validam sem `version` e sem profiles;
- o container fica saudável e responde pela rede no alias e porta corretos;
- o proxy externo consegue abrir a interface e manter WebSocket;
- reiniciar ou recriar o container preserva `config/`;
- configuração existente impede restauração;
- ambiente vazio com backup válido é restaurado;
- ambiente vazio sem backup abre instalação nova;
- backups inválidos falham sem deixar restauração parcial;
- Jenkins ignora `main` e implanta apenas a branch correta;
- GitHub Actions não depende do `.env` da VPS;
- verificações, testes, build, smoke, regressão e E2E passam;
- `README.md` permite que uma pessoa opere o projeto;
- este `AGENTS.md`, sozinho, contém informações suficientes para um agente reconstruir o sistema sem acesso ao código original.
