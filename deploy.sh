#!/usr/bin/env bash
# PulseGuard - redespliegue en un comando (rama deploy/web)
set -euo pipefail
cd "$(dirname "$0")"

echo "==> 1/4 Actualizando código"
git fetch origin
git reset --hard origin/deploy/web
git log --oneline -1

echo "==> 2/4 Construyendo y levantando contenedores"
docker compose up -d --build --remove-orphans

echo "==> 3/4 Reiniciando proxy (por si cambió la configuracion)"
docker compose restart nginx

echo "==> 4/4 Estado"
sleep 5
docker compose ps
echo
echo "Listo. Abre https://pulseguard.sweetcode.studio"
