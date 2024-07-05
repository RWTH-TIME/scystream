FROM node:lts-alpine AS installer

WORKDIR /app

COPY package.json ./

RUN npm install

##

FROM node:lts-alpine AS builder

WORKDIR /app

COPY . .

COPY --from=installer /app/node_modules ./node_modules

RUN npm run build

##

FROM node:lts-alpine
WORKDIR /app

ARG PORT=80

ENV PORT ${PORT}

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE ${PORT}

CMD npm start -- -p $PORT
