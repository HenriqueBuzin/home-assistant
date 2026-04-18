#!/bin/bash

CONFIG_FILE="/config/configuration.yaml"
EXTERNAL_URL=${HA_URL}

mkdir -p /config

cat <<EOF > "$CONFIG_FILE"
default_config:

frontend:
  themes: !include_dir_merge_named themes

homeassistant:
  external_url: "${EXTERNAL_URL}"
  internal_url: "http://127.0.0.1:8123"

http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - 172.16.0.0/12
    - 172.18.0.0/16
EOF

exec /init
