ARG PY_VERSION="3.12" 

FROM python:${PY_VERSION}-alpine AS builder

ENV PIP_NO_WARN_ABOUT_ROOT_USER 1

WORKDIR /build

RUN apk update && apk upgrade --no-cache && apk add gcc musl-dev libffi-dev libressl-dev && apk add gcc musl-dev libffi-dev libressl-dev

COPY requirements.txt /build

RUN pip install --prefix=/build/venv --no-cache-dir --upgrade -r requirements.txt

##

FROM python:${PY_VERSION}-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT=4000 

ENV UVICORN_HOST="0.0.0.0"
ENV UVICORN_PORT=$PORT

RUN apk update && apk upgrade --no-cache && apk add gcc musl-dev libffi-dev libressl-dev

COPY --from=builder /build/venv /usr/local/
COPY . /app

WORKDIR /app

ENTRYPOINT ["uvicorn", "main:app", "--proxy-headers"]
