FROM node:22.17-alpine AS installer

WORKDIR /app

COPY package.json package-lock.json ./

RUN npm install

FROM node:22.17-alpine AS builder

WORKDIR /app

COPY . .

COPY --from=installer /app/node_modules ./node_modules

RUN npm run build

FROM node:22.17-alpine

WORKDIR /app

ENV PORT=80 \
    NODE_ENV=production

COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE ${PORT}

CMD ["sh", "-c", "npm start -- -p $PORT"]
