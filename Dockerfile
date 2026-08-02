# syntax=docker/dockerfile:1.7

FROM node:24.18.1-bookworm-slim AS verify

WORKDIR /workspace

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . ./

RUN npm run test:e2e:list


FROM ghcr.io/home-assistant/home-assistant:2026.7.4 AS runtime

RUN apk upgrade --no-cache

COPY init.sh /usr/local/bin/init-home-assistant
COPY scripts/restore-backup.py /usr/local/bin/restore-home-assistant
COPY scripts/restore-backup.py scripts/test-restore-backup.py \
    scripts/check-vulnerability-baseline.py scripts/test-vulnerability-baseline.py \
    /tmp/infra-tests/
RUN python3 /tmp/infra-tests/test-restore-backup.py \
    && python3 /tmp/infra-tests/test-vulnerability-baseline.py \
    && rm -rf /tmp/infra-tests \
    && chmod 0755 /usr/local/bin/init-home-assistant /usr/local/bin/restore-home-assistant

ENTRYPOINT ["/usr/local/bin/init-home-assistant"]
