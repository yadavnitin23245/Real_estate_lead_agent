#!/bin/sh
set -e
cd /app

# Reinstall only when package-lock.json changed since the last successful install.
STAMP=node_modules/.lock-hash
HASH=$(sha1sum package-lock.json | cut -d' ' -f1)

if [ ! -x node_modules/.bin/vite ] || [ "$(cat "$STAMP" 2>/dev/null)" != "$HASH" ]; then
  echo "==> Installing frontend dependencies (first start or lockfile changed)"
  ok=0
  for i in 1 2 3; do
    if npm install --no-audit --no-fund \
        && [ -x node_modules/.bin/vite ]; then
      ok=1; break
    fi
    echo "npm install failed (attempt $i/3); retrying - downloaded packages are cached"
    sleep 3
  done
  [ "$ok" = 1 ] || { echo "Could not install dependencies; check network access to registry.npmjs.org"; exit 1; }
  echo "$HASH" > "$STAMP"
fi

exec npm run dev -- --host 0.0.0.0
