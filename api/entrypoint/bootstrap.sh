#!/bin/bash

set -o errexit
set -o nounset

echo "Waiting for PostgreSQL"
. ./entrypoint/wait-postgres.sh

echo "Waiting for Elasticsearch"
. ./entrypoint/wait-elasticsearch.sh

echo "Running migrations"
python manage.py migrate

echo "Loading fixtures"
python manage.py loaddata ./fixtures/*.json

