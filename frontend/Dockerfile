FROM node:22-alpine
WORKDIR /app
# Node 20+ "happy eyeballs" gives each connect attempt only 250 ms, which makes npm
# time out on high-latency networks (and Docker Desktop often has no IPv6 route).
ENV NODE_OPTIONS="--dns-result-order=ipv4first --no-network-family-autoselection"
COPY docker-entrypoint.sh /usr/local/bin/frontend-entrypoint
RUN sed -i 's/\r$//' /usr/local/bin/frontend-entrypoint && chmod +x /usr/local/bin/frontend-entrypoint
EXPOSE 5173
# Dependencies are installed on first start into the node_modules volume (see entrypoint),
# so a slow or flaky network never breaks `docker compose build`.
CMD ["frontend-entrypoint"]
