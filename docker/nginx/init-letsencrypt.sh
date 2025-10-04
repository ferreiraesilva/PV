#!/bin/bash
set -euo pipefail

COMPOSE_FILE=${COMPOSE_FILE:-docker-compose.yml}
PROFILES=${COMPOSE_PROFILES:-prod}
export COMPOSE_PROFILES=${PROFILES}
COMPOSE="docker compose -f ${COMPOSE_FILE}"

API_DOMAIN=${API_SERVER_NAME:-api.labs4ideas.com.br}
FRONTEND_DOMAIN=${FRONTEND_SERVER_NAME:-pv.labs4ideas.com.br}
WWW_DOMAIN=${WWW_SERVER_NAME:-www.labs4ideas.com.br}
EMAIL=${LETSENCRYPT_EMAIL:-}
STAGING=${LETSENCRYPT_STAGING:-0}
RSA_KEY_SIZE=${LETSENCRYPT_KEY_SIZE:-4096}

DOMAINS=($API_DOMAIN $FRONTEND_DOMAIN $WWW_DOMAIN)

if [ -z "$EMAIL" ]; then
  echo "[letsencrypt] WARNING: no email provided (set LETSENCRYPT_EMAIL). Using --register-unsafely-without-email."
  EMAIL_ARGS=("--register-unsafely-without-email")
else
  EMAIL_ARGS=("--email" "$EMAIL" "--agree-tos")
fi

STAGING_ARGS=()
if [ "$STAGING" != "0" ]; then
  echo "[letsencrypt] Using Let's Encrypt staging environment"
  STAGING_ARGS=("--staging")
fi

DOMAIN_ARGS=()
for domain in "${DOMAINS[@]}"; do
  if [ -n "$domain" ]; then
    DOMAIN_ARGS+=("-d" "$domain")
  fi
done

if [ ${#DOMAIN_ARGS[@]} -eq 0 ]; then
  echo "[letsencrypt] No domains configured. Aborting."
  exit 1
fi

read -p "This will request certificates for: ${DOMAINS[*]}. Continue? [y/N] " decision
if [[ ! $decision =~ ^[Yy]$ ]]; then
  echo "Aborted by user"
  exit 0
fi

${COMPOSE} up -d nginx

${COMPOSE} run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  "${DOMAIN_ARGS[@]}" \
  "${EMAIL_ARGS[@]}" \
  "${STAGING_ARGS[@]}" \
  --rsa-key-size ${RSA_KEY_SIZE} \
  --non-interactive \
  --force-renewal

${COMPOSE} exec nginx nginx -s reload

echo "[letsencrypt] Certificates issued. Remember to update DNS records to point to this host."
