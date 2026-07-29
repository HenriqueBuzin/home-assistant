# syntax=docker/dockerfile:1.7

FROM node:24.18.0-bookworm-slim AS verify

WORKDIR /workspace

COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY . ./

RUN npm run test:e2e:list


FROM ghcr.io/home-assistant/home-assistant:2026.7.4 AS runtime

COPY init.sh /usr/local/bin/init-home-assistant
RUN chmod 0755 /usr/local/bin/init-home-assistant

ENTRYPOINT ["/usr/local/bin/init-home-assistant"]
