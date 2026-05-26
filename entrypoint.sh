#!/bin/bash
set -euo pipefail

python manage.py wait_for_database

type="${1:-prod}"

if [ "$type" = "dev" ]; then
  python manage.py migrate
  exec python manage.py runserver 0.0.0.0:8000 --force-color
else
  python manage.py migrate
  exec /base/gunicorn.sh sortiment.wsgi
fi
