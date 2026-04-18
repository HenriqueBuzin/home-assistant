#!/bin/bash

CONFIG_FILE="/config/configuration.yaml"

echo "🔧 Definindo configuração completa do Home Assistant..."

cat <<EOF > "$CONFIG_FILE"
default_config:

frontend:
  themes: !include_dir_merge_named themes

automation: !include automations.yaml
script: !include scripts.yaml
scene: !include scenes.yaml

http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - 172.16.0.0/12
EOF

exec /init
