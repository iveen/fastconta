# app/frontend/Dockerfile

# ==============================================================================
# ETAPA 1: Construcción (Builder)
# ==============================================================================
FROM node:24-alpine AS builder

# Habilitar corepack para usar pnpm de forma nativa y segura
RUN corepack enable

WORKDIR /app

# Copiar archivos de manifiesto primero para aprovechar la cache
COPY package.json pnpm-lock.yaml ./

# Instalar dependencias de forma congelada (segura y rapida)
RUN pnpm install --frozen-lockfile

# Copiar el resto del codigo y construir
COPY . .
RUN pnpm run build

# ==============================================================================
# ETAPA 2: Producción (Servidor Nginx ligero)
# ==============================================================================
FROM nginx:alpine

# Copiar archivos construidos (dist) al directorio de Nginx
COPY --from=builder /app/dist /usr/share/nginx/html

# Copiar configuracion personalizada de Nginx (ver paso 3)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]