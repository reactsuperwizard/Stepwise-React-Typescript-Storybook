#!/bin/bash

set -o errexit
set -o nounset

elasticsearch_ready() {
python << END
import sys
import requests

try:
    requests.get("http://${ELASTICSEARCH_URL}/_cat/health?h=st")
except requests.exceptions.ConnectionError as e:
    print(e)
    sys.exit(-1)
sys.exit(0)
END
}
until elasticsearch_ready; do
  >&2 echo 'Waiting for Elasticsearch to become available...'
  sleep 1
done
>&2 echo 'Elasticsearch is available'