FROM node:22-alpine
WORKDIR /app/api

ENV NODE_ENV=development

# Install deps with caching
COPY package.json package-lock.json* ./
RUN --mount=type=cache,target=/root/.npm npm ci

# Copy tsconfig and source (in dev we will also bind-mount, but having files helps)
COPY tsconfig.json ./
COPY src ./src

EXPOSE 3001
# default cmd comes from docker-compose: npm run dev
