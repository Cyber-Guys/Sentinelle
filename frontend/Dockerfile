# syntax=docker/dockerfile:1
# Produzione: app Nuxt (ssr: false) compilata in statico e servita da nginx: a runtime niente Node,
# pochi MB di RAM. nginx inoltra anche /api al backend (sostituisce il proxy di Nitro) e serve i tile con Range.
# Sviluppo (target "dev", vedi compose.dev.yaml): nuxt dev con hot reload, sorgenti montati da compose.
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --no-audit --no-fund

FROM deps AS dev
CMD ["npm", "run", "dev"]

FROM deps AS build
COPY . .
RUN npx nuxt generate

FROM nginx:1.30-alpine
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/.output/public /usr/share/nginx/html
