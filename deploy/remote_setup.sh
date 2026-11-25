#!/usr/bin/env bash
# Remote setup for CampusEvent on a Vibe Hosting container.
# Uploaded and executed by deploy.ps1. No secrets are committed here.
set -euo pipefail

echo "== hostname =="
hostname
test -d /root/www

mkdir -p /root/myapp
tar -xzf /root/deploy.tar.gz -C /root/myapp
cd /root/myapp

echo "== python =="
python3 -V
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi

echo "== dependencies =="
.venv/bin/pip install -q --upgrade pip || true
.venv/bin/pip install -q -r requirements.txt gunicorn

echo "== database =="
mkdir -p /root/myapp/instance
export CAMPUSEVENT_DATABASE=/root/myapp/instance/campus_event.db
export CAMPUSEVENT_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(24))')"
.venv/bin/python cli.py init-db
.venv/bin/python cli.py seed-demo || true

echo "== run.sh =="
SECRET=$(python3 -c 'import secrets; print(secrets.token_hex(24))')
cat > /root/run.sh <<SH
#!/usr/bin/env bash
cd /root/myapp
export CAMPUSEVENT_DATABASE=/root/myapp/instance/campus_event.db
export CAMPUSEVENT_SECRET_KEY=${SECRET}
export CAMPUSEVENT_ADMIN_PASSWORD=admin123
exec .venv/bin/gunicorn --bind 0.0.0.0:80 --workers 1 --threads 2 --timeout 60 'app:create_app()'
SH
chmod 755 /root/run.sh

echo "== restart =="
pkill -f '[r]un.sh' || true
sleep 6

echo "== local check =="
for attempt in 1 2 3 4 5; do
  code=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1/healthz || true)
  echo "attempt $attempt -> HTTP $code"
  [ "$code" = "200" ] && break
  sleep 4
done
curl -s http://127.0.0.1/healthz
echo
