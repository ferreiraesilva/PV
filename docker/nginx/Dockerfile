FROM nginx:1.26-alpine

RUN apk add --no-cache bash gettext

COPY nginx.conf /etc/nginx/nginx.conf
COPY snippets /etc/nginx/snippets
COPY templates /etc/nginx/templates
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

VOLUME ["/etc/letsencrypt", "/var/www/certbot"]

EXPOSE 80 443

ENTRYPOINT ["/entrypoint.sh"]
