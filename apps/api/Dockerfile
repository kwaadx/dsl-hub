FROM node:24-alpine

RUN apk add --no-cache openssl

WORKDIR /app/api

COPY package*.json tsconfig.json ./
RUN npm ci

COPY prisma ./prisma
RUN npx prisma generate

COPY src ./src

EXPOSE 3001

CMD ["npm", "run", "dev"]
