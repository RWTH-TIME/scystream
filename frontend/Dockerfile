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

ENV PORT=80

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 80

CMD npm start -- -p $PORT
