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
  docker compose --env-file .env.example -f "$file" config --quiet
done

for service in backend web; do
  grep -Eq "^  ${service}:$" docker-compose.yml
  grep -Eq "^  ${service}:$" docker-compose-prod.yml
done
