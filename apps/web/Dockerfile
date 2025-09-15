FROM node:lts-alpine

WORKDIR /app/web

RUN npm install -g @vue/cli@5.0.9 vite

COPY package.json .
COPY package-lock.json .

RUN npm install
RUN npm install -g npm@11.6.0

CMD ["npm", "run", "dev"]
