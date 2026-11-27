#!/bin/sh
set -eu

IMAGE="$1"
BACKUP="devops-manager-backup-${BUILD_NUMBER}"
DATA="/home/devasc/devops-final/data"

echo "Validando nueva imagen..."

docker run --rm \
  --group-add 1001 \
  -v "$DATA:/app/data:ro" \
  "$IMAGE" \
  python -c 'from app import app; assert app.test_client().get("/").status_code == 200'

docker rename devops-manager "$BACKUP"

rollback() {
    echo "Restaurando version anterior..."
    docker rm -f devops-manager 2>/dev/null || true
    docker rename "$BACKUP" devops-manager
    docker start devops-manager
}

trap rollback EXIT

docker stop "$BACKUP"

docker run -d \
  --name devops-manager \
  --restart unless-stopped \
  --group-add 1001 \
  --security-opt no-new-privileges:true \
  --cap-drop ALL \
  -p 127.0.0.1:8080:8080 \
  -v "$DATA:/app/data:ro" \
  "$IMAGE"

for intento in $(seq 1 15); do
    if docker run --rm --network host "$IMAGE" python -c 'import urllib.request; r=urllib.request.urlopen("http://127.0.0.1:8080/", timeout=3); assert r.status == 200' 2>/dev/null; then
        trap - EXIT
        echo "HTTP 200 - Servicio operativo"
        echo "Despliegue exitoso"
        exit 0
    fi
    sleep 2
done

echo "Error en la verificacion HTTP"
exit 1
