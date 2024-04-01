FROM node:21.7.1-alpine AS cssbuild

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

ARG MULTIRUN_VERSION=1.1.3
ADD https://github.com/nicolas-van/multirun/releases/download/${MULTIRUN_VERSION}/multirun-x86_64-linux-gnu-${MULTIRUN_VERSION}.tar.gz /tmp
RUN tar -xf /tmp/multirun-x86_64-linux-gnu-${MULTIRUN_VERSION}.tar.gz \
    && mv multirun /bin \
    && rm /tmp/*

RUN chown appuser:appuser /app

USER appuser

RUN pip install --upgrade pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --dev --deploy

COPY sortiment ./sortiment
COPY --from=cssbuild /app/sortiment/static/* /app/sortiment/static/

COPY docker/start.sh /app/start.sh
COPY docker/Caddyfile /app/Caddyfile

WORKDIR /app/sortiment
RUN python manage.py collectstatic --no-input
CMD ["/bin/multirun", "caddy run --adapter caddyfile --config /app/Caddyfile", "/app/start.sh"]
