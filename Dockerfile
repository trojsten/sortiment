FROM node:lts-alpine AS cssbuild

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && \
 pnpm install --ignore-scripts --frozen-lockfile

COPY sortiment ./sortiment
COPY tailwind.config.js ./
RUN pnpm run build
CMD ["pnpm", "run", "watch"]

FROM ghcr.io/trojsten/django-docker:v8

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-cache

COPY . /app
COPY --from=cssbuild /app/sortiment/style/static/* /app/sortiment/style/static/

RUN python manage.py collectstatic --no-input
ENV BASE_START=/app/entrypoint.sh
