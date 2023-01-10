#!/bin/bash

set -o errexit
set -o nounset

echo "Waiting for PostgreSQL"
. ./entrypoint/wait-postgres.sh

echo "Waiting for Elasticsearch"
. ./entrypoint/wait-elasticsearch.sh

echo "Running migrations"
python manage.py migrate

echo "Running dev server"
python manage.py runserver_plus 0.0.0.0:8000
