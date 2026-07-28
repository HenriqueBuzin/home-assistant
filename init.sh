#!/bin/sh
set -eu

config_file="/config/configuration.yaml"
external_url="${HA_URL:?Defina HA_URL}"

mkdir -p /config

if [ ! -f "$config_file" ]; then
cat <<EOF > "$config_file"
default_config:

frontend:
  themes: !include_dir_merge_named themes

homeassistant:
  external_url: "${external_url}"
  internal_url: "http://127.0.0.1:8123"

http:
  use_x_forwarded_for: true
  trusted_proxies:
    - 127.0.0.1
    - 172.16.0.0/12
    - 172.18.0.0/16
EOF
fi

exec /init
