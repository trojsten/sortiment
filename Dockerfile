FROM node:21.6.2-alpine AS cssbuild

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY sortiment ./sortiment
COPY tailwind.config.js ./
RUN npm run css-prod
CMD ["npm", "run", "css-dev"]

FROM python:3.12-slim-bookworm

WORKDIR /app
RUN useradd --create-home appuser

ENV PYTHONUNBUFFERED 1
ENV PYTHONFAULTHANDLER 1
ENV PATH=/home/appuser/.local/bin:$PATH

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt update \
    && apt install -y caddy xz-utils \
    && apt -y upgrade \
    && apt -y clean \
    && rm -rf /var/lib/apt/lists/*

ARG S6_OVERLAY_VERSION=3.1.6.2
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz
ADD https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-x86_64.tar.xz /tmp
RUN tar -C / -Jxpf /tmp/s6-overlay-x86_64.tar.xz

RUN chown appuser:appuser /app

USER appuser

RUN pip install --upgrade pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --dev --deploy

COPY sortiment ./sortiment
COPY --from=cssbuild /app/sortiment/static/* /app/sortiment/static/

COPY docker/s6 /etc/s6-overlay/s6-rc.d
COPY docker/Caddyfile /app/Caddyfile

WORKDIR /app/sortiment
RUN python manage.py collectstatic --no-input
CMD ["/init"]
