#!/bin/bash

CONFIG_FILE="/config/configuration.yaml"
EXTERNAL_URL=${HA_URL}

echo "🔧 Configurando Home Assistant para ${EXTERNAL_URL}..."

mkdir -p /config
touch "$CONFIG_FILE"

# Se já tiver external_url, NÃO faz nada
if grep -q "external_url" "$CONFIG_FILE"; then
  echo "⚠️ external_url já existe, não vou alterar."
else

  echo "➕ Adicionando configuração..."

  cat <<EOF >> "$CONFIG_FILE"

homeassistant:
  external_url: "${EXTERNAL_URL}"
  internal_url: "http://127.0.0.1:8123"

http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - 172.16.0.0/12

    # Cloudflare IPv4
    - 103.21.244.0/22
    - 103.22.200.0/22
    - 103.31.4.0/22
    - 104.16.0.0/13
    - 104.24.0.0/14
    - 108.162.192.0/18
    - 131.0.72.0/22
    - 141.101.64.0/18
    - 162.158.0.0/15
    - 172.64.0.0/13
    - 173.245.48.0/20
    - 188.114.96.0/20
    - 190.93.240.0/20
    - 197.234.240.0/22
    - 198.41.128.0/17
EOF

fi

echo "✅ Config final:"
cat "$CONFIG_FILE"

exec /init
