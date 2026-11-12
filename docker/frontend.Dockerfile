# Build stage. Base images are pinned by digest (multi-arch index current on 2026-10-14); Dependabot bumps them.
FROM node:24.22.2-alpine3.24@sha256:a34ab6d7f6f4813f4d0c5469d74685604b962fbdbf5793a7bc7b4998ecb867c8 AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm ci

# Copy source code and build
COPY frontend/ .
RUN npm run build

# Production stage
FROM nginxinc/nginx-unprivileged:1.31.7-alpine3.24@sha256:b5047b9b76845eac124358373c6852377c52e4b05834a47647e955dd91cb8f1e

# Copy built assets to Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the server proxy configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# The API key header (TCK-20261112-COMPOSE-STACK-HAS-NO-API-KEY). A one-line template that the base image's entrypoint (20-envsubst-on-templates.sh, which
# runs as uid 101) renders at container start into /tmp/api-key.conf; nginx.conf includes that file inside `location /api/`. Only variables whose names start
# with FRONTEND_API_KEY are substituted, so nginx's own $variables are never touched. The key comes from the container's environment at start (compose loads
# FRONTEND_API_KEY from the gitignored docker/secrets/compose.env, over the empty default in docker/frontend.defaults.env); it is never in the image. An empty value renders `proxy_set_header X-API-Key "";`, which sends no header.
COPY docker/nginx-api-key.conf.template /etc/nginx/templates/api-key.conf.template
ENV NGINX_ENVSUBST_OUTPUT_DIR=/tmp
ENV NGINX_ENVSUBST_FILTER=^FRONTEND_API_KEY

# The unprivileged image listens on 8080 and runs as uid 101 (TCK-20261019-DEPLOY-DOCS-SHA-PINS-AND-FRONTEND-NONROOT)
USER 101
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
