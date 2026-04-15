#!/bin/bash
set -e

influxd &
INFLUXD_PID=$!

echo "Waiting for InfluxDB to start..."
for i in {1..30}; do
    if curl -fsS http://localhost:8086/health >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

ORG="${ORG:-int_org}"
BUCKET="${BUCKET:-int_bucket}"
USERNAME="${USERNAME:-int_user}"
PASSWORD="${PASSWORD:-int_password}"
TOKEN="${ADMIN_TOKEN:-int_token}" 

influx setup \
  --username ${USERNAME} \
  --password ${PASSWORD} \
  --token ${TOKEN} \
  --org ${ORG} \
  --bucket ${BUCKET} \
  --force

influx config create \
  --config-name int_config \
  --host-url http://localhost:8086 \
  --org ${ORG} \
  --token ${TOKEN} 
