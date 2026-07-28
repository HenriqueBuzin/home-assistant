# syntax=docker/dockerfile:1.7

FROM ghcr.io/home-assistant/home-assistant:2026.7.4

COPY init.sh /usr/local/bin/init-home-assistant
RUN chmod 0755 /usr/local/bin/init-home-assistant

ENTRYPOINT ["/usr/local/bin/init-home-assistant"]
