#!/bin/bash

CONFIG_FILE="/config/configuration.yaml"

EXTERNAL_URL=${HA_URL}

echo "🔧 Configurando Home Assistant para ${EXTERNAL_URL}..."

if ! grep -q "external_url" "$CONFIG_FILE" 2>/dev/null; then

  cat <<EOF >> "$CONFIG_FILE"

homeassistant:
  external_url: "${EXTERNAL_URL}"
  internal_url: "http://127.0.0.1:8123"

http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - 172.16.0.0/12
EOF

fi

exec /init
