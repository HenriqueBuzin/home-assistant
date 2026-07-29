#!/bin/sh
set -eu

export HA_SITE="${HA_SITE:-ci}"
export HA_URL="${HA_URL:-https://ha.example.test}"
export HA_CONFIG_ROOT="${HA_CONFIG_ROOT:-/tmp/home-assistant-ci}"

sh -n init.sh

for file in docker-compose.yml docker-compose-prod.yml; do
  ! grep -Eq '^[[:space:]]*version:' "$file"
  ! grep -Eq '^[[:space:]]*profiles:' "$file"
  ! grep -Eqi 'nginx' "$file"
  ! grep -Eqi 'caddy' "$file"
  docker compose --env-file .env.example -f "$file" config --quiet
done

for service in backend; do
  grep -Eq "^  ${service}:$" docker-compose.yml
  grep -Eq "^  ${service}:$" docker-compose-prod.yml
done

grep -Eq 'home-assistant-\$\{HA_SITE\}-dev' docker-compose.yml
grep -Eq 'home-assistant-\$\{HA_SITE\}' docker-compose-prod.yml
grep -Eq '"8123"' docker-compose.yml
grep -Eq '"8123"' docker-compose-prod.yml
