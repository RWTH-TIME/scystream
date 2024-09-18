FROM node:lts-alpine AS installer

WORKDIR /app

COPY package.json ./

RUN npm install

##

FROM node:lts-alpine AS builder

WORKDIR /app

COPY . .

COPY --from=installer /app/node_modules ./node_modules

# NEXT_PUBLIC previxed env variables have to be set at built time
ARG NEXT_PUBLIC_API_URL=http://localhost:4000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

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
