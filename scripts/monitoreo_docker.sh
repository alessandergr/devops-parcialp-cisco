#!/bin/sh
set -eu
umask 077

BASE="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="$(/usr/bin/docker inspect \
  --format '{{.Image}}' devops-manager)"
GID="$(getent group netops | cut -d: -f3)"

exec 9>"$BASE/logs/.monitoreo.lock"
flock -n 9 || exit 0

/usr/bin/docker run --rm \
  --user "$(id -u):$GID" \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  -v "$BASE/.env:/app/.env:ro" \
  -v "$BASE/data:/app/data" \
  -v "$BASE/logs:/app/logs" \
  "$IMAGE" python src/monitoring.py
