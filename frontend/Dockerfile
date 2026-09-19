# --- Frontend Dockerfile (multi-stage: build + nginx serve) ---
FROM node:20-slim AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
COPY --from=build /app/dist /usr/share/nginx/html
# NOT: infra/nginx.conf, reverse-proxy (ayri nginx servisi) icindir.
# Bu container kendi varsayilan nginx config'i ile statik dosyalari sunar.
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
