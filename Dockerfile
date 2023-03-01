FROM node:19.7.0-alpine AS cssbuild

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY sortiment ./sortiment
COPY tailwind.config.js ./
RUN npm run css-prod
CMD ["npm", "run", "css-dev"]

FROM python:3.11-slim-bullseye
WORKDIR /app
RUN useradd --create-home appuser

ENV PYTHONUNBUFFERED 1
ENV PYTHONFAULTHANDLER 1
ENV PATH=/home/appuser/.local/bin:$PATH

RUN export DEBIAN_FRONTEND=noninteractive \
    && apt update \
    && apt -y upgrade \
    && apt -y clean \
    && rm -rf /var/lib/apt/lists/*

USER appuser

RUN pip install --upgrade pipenv
COPY Pipfile Pipfile.lock ./
RUN pipenv install --system --dev --deploy

COPY sortiment ./sortiment
COPY --from=cssbuild /app/sortiment/static/* /app/sortiment/static/

WORKDIR /app/sortiment
CMD ["gunicorn", "sortiment.wsgi", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--log-file", "-", "--workers", "4"]
