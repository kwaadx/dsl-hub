FROM node:lts-alpine

WORKDIR /dsl-hub/web

RUN npm install -g @vue/cli@5.0.8 vite

COPY package.json .
COPY package-lock.json .

RUN npm install
RUN npm install -g npm@11.0.0

CMD ["npm", "run", "dev"]
