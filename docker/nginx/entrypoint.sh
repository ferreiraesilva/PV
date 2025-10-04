#!/bin/sh
set -eu

TEMPLATES_DIR="/etc/nginx/templates"
OUTPUT_DIR="/etc/nginx/conf.d"

mkdir -p "$OUTPUT_DIR"

if [ -d "$TEMPLATES_DIR" ]; then
  for template in "$TEMPLATES_DIR"/*.template; do
    [ -e "$template" ] || continue
    output="$OUTPUT_DIR/$(basename "${template%.template}").conf"
    echo "[nginx-entrypoint] Rendering $(basename "$template") -> $(basename "$output")"
    envsubst '
      ${API_SERVER_NAME}
      ${FRONTEND_SERVER_NAME}
      ${WWW_SERVER_NAME}
      ${BACKEND_UPSTREAM}
      ${FRONTEND_UPSTREAM}
      ${WWW_UPSTREAM_URL}
      ${WWW_PROXY_HOST}
    ' <"$template" >"$output"
  done
fi

exec nginx -g 'daemon off;'
