# Production front image: build the Vite dist, serve it with nginx, and
# proxy /api + /ws to the pushpin container over the kamal docker network.
# Built by Kamal from the repo root (see config/deploy.front.yml).
FROM node:22-slim AS build
WORKDIR /app
COPY front/package.json front/package-lock.json ./
RUN npm ci
COPY front/ ./
RUN npm run build

FROM nginx:stable-alpine
COPY .docker/front-production/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
