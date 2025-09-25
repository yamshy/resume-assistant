# syntax=docker/dockerfile:1.7

FROM oven/bun:1 as build
WORKDIR /app

COPY bun.lock package.json ./
RUN bun install --frozen-lockfile

COPY . ./
ENV VITE_API_URL=/api
RUN bun run build

FROM caddy:2.10-alpine AS runtime

ARG APP_VERSION=0.0.0
ARG REPOSITORY=resume-assistant-ui/resume-assistant-ui
LABEL org.opencontainers.image.source="https://github.com/${REPOSITORY}" \
      org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.title="resume-assistant-ui" \
      org.opencontainers.image.description="Svelte-based resume assistant UI"

COPY Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /usr/share/caddy

EXPOSE 80
