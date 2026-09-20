#!/usr/bin/env bash
# PulseGuard - redespliegue en un comando (rama deploy/web)
set -euo pipefail
umask 022
cd "$(dirname "$0")"

echo "==> 1/4 Actualizando código"
git fetch origin
git reset --hard origin/deploy/web
chmod -R a+rX web
git log --oneline -1

echo "==> 2/4 Construyendo y levantando contenedores"
docker compose up -d --build --remove-orphans

echo "==> 2b/4 Migrando: quitar FK de admissions (permite paciente/póliza nuevos)"
docker exec pulseguard-db psql -U pulseguard -d pulseguard -c \
  "ALTER TABLE admissions DROP CONSTRAINT IF EXISTS admissions_patient_id_fkey; ALTER TABLE admissions DROP CONSTRAINT IF EXISTS admissions_policy_number_fkey;" >/dev/null 2>&1 || true

echo "==> 3/4 Reiniciando proxy (por si cambió la configuracion)"
docker compose restart nginx

echo "==> 4/4 Estado"
sleep 5
docker compose ps
echo
echo "Listo. Abre https://pulseguard.sweetcode.studio"
