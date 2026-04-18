FROM ghcr.io/home-assistant/home-assistant:stable

COPY init.sh /init-proxy.sh
RUN chmod +x /init-proxy.sh

ENTRYPOINT ["/init-proxy.sh"]
