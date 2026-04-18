#!/bin/bash

CONFIG_FILE="/config/configuration.yaml"

if ! grep -q "use_x_forwarded_for" "$CONFIG_FILE" 2>/dev/null; then
  echo "🔧 Configurando proxy no Home Assistant..."

  cat <<EOF >> "$CONFIG_FILE"

http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - 172.16.0.0/12
EOF
fi

exec /init
