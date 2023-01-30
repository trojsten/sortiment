#!/bin/bash
# Wait for database to be up
while :
do
    (echo -n > /dev/tcp/db/5432) >/dev/null 2>&1
    if [[ $? -eq 0 ]]; then
        break
    fi
    sleep 1
done

set -euo pipefail
python manage.py migrate
exec python manage.py runserver 0.0.0.0:8000
