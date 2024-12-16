FROM node:23-alpine AS cssbuild

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm
RUN pnpm install

COPY sortiment ./sortiment
COPY tailwind.config.js ./
RUN pnpm run prod
CMD ["pnpm", "run", "dev"]

FROM python:3.12-slim-bookworm

WORKDIR /app
RUN useradd --create-home appuser

ENV PYTHONUNBUFFERED 1
ENV PYTHONFAULTHANDLER 1

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt update \
    && apt install -y caddy xz-utils \
    && apt -y upgrade \
    && apt -y clean \
    && rm -rf /var/lib/apt/lists/*

ARG MULTIRUN_VERSION=1.1.3
ADD https://github.com/nicolas-van/multirun/releases/download/${MULTIRUN_VERSION}/multirun-x86_64-linux-gnu-${MULTIRUN_VERSION}.tar.gz /tmp
RUN tar -xf /tmp/multirun-x86_64-linux-gnu-${MULTIRUN_VERSION}.tar.gz \
    && mv multirun /bin \
    && rm /tmp/*

RUN chown appuser:appuser /app

ENV POETRY_VIRTUALENVS_CREATE 0
RUN pip install --upgrade poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root

USER appuser

COPY sortiment ./sortiment
COPY --from=cssbuild /app/sortiment/static/* /app/sortiment/static/

COPY docker/start.sh /app/start.sh
COPY docker/Caddyfile /app/Caddyfile

WORKDIR /app/sortiment
RUN python manage.py collectstatic --no-input
CMD ["/bin/multirun", "caddy run --adapter caddyfile --config /app/Caddyfile", "/app/start.sh"]
