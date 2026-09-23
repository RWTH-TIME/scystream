# syntax=docker/dockerfile:1
ARG PY_VERSION="3.14"

FROM python:${PY_VERSION}-alpine AS builder
WORKDIR /build
RUN apk add --no-cache gcc musl-dev libffi-dev
COPY requirements.txt .
# requirements only change with requirements.txt, so this layer is cached;
# the pip cache survives changed requirements between builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefix=/install -r requirements.txt


FROM python:${PY_VERSION}-alpine
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    HOST=0.0.0.0

# git & ssh: compute block and template repositories are cloned at runtime
RUN apk upgrade --no-cache && apk add --no-cache git openssh-client \
    && adduser -D -u 50000 -G root -h /home/core core

COPY --from=builder /install /usr/local
WORKDIR /app
COPY --chown=core:root . .
RUN mkdir -p /app/repos /airflow-dags \
    && chown core:root /app/repos /airflow-dags

USER core
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn main:app --proxy-headers --forwarded-allow-ips \"${FORWARDED_ALLOW_IPS:-127.0.0.1}\" --host \"$HOST\" --port \"$PORT\""]
