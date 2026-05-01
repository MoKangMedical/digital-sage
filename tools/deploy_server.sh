#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST="${HOST:-root@43.134.3.158}"
REMOTE_ROOT="${REMOTE_ROOT:-/srv/digital-sage}"
REMOTE_APP_DIR="$REMOTE_ROOT/current"
SSH_KEY="${SSH_KEY:-}"
SSH_OPTS=(-o StrictHostKeyChecking=accept-new -o IdentitiesOnly=yes)

if [[ -n "$SSH_KEY" ]]; then
  SSH_OPTS+=(-i "$SSH_KEY")
fi

if [[ -f "$ROOT_DIR/.env.local" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env.local"
  set +a
elif [[ -f "$ROOT_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT_DIR/.env"
  set +a
fi

: "${MIMO_API_KEY:?MIMO_API_KEY is required in .env.local or environment}"
MIMO_API_BASE="${MIMO_API_BASE:-https://api.xiaomimimo.com/v1}"

echo "==> Preparing remote directories"
ssh "${SSH_OPTS[@]}" "$HOST" "mkdir -p '$REMOTE_ROOT' '$REMOTE_APP_DIR'"

echo "==> Uploading project"
rsync -az --delete \
  --exclude '.git' \
  --exclude '.env' \
  --exclude '.env.local' \
  --exclude '__pycache__' \
  --exclude '.DS_Store' \
  --exclude 'media/demo/_build' \
  -e "ssh ${SSH_OPTS[*]}" \
  "$ROOT_DIR/" "$HOST:$REMOTE_APP_DIR/"

echo "==> Writing runtime environment"
ssh "${SSH_OPTS[@]}" "$HOST" "cat > '$REMOTE_APP_DIR/.env' <<'EOF'
MIMO_API_BASE=$MIMO_API_BASE
MIMO_API_KEY=$MIMO_API_KEY
EOF"

echo "==> Installing runtime dependencies and service"
ssh "${SSH_OPTS[@]}" "$HOST" "bash -se" <<'REMOTE'
set -euo pipefail

REMOTE_ROOT="/srv/digital-sage"
REMOTE_APP_DIR="$REMOTE_ROOT/current"

install_base_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get install -y python3 python3-venv python3-pip nginx curl
    return
  fi

  if command -v dnf >/dev/null 2>&1; then
    dnf install -y python3 python3-pip nginx curl
    return
  fi

  if command -v yum >/dev/null 2>&1; then
    yum install -y python3 python3-pip nginx curl
    return
  fi

  echo "No supported package manager found on remote host" >&2
  exit 1
}

install_base_packages

python3 -m venv "$REMOTE_ROOT/venv"
"$REMOTE_ROOT/venv/bin/pip" install --upgrade pip
"$REMOTE_ROOT/venv/bin/pip" install -r "$REMOTE_APP_DIR/requirements.txt"

install -m 0644 "$REMOTE_APP_DIR/deploy/digital-sage.service" /etc/systemd/system/digital-sage.service
if [[ -f /etc/letsencrypt/live/digitalsage.cloud/fullchain.pem && -f /etc/letsencrypt/live/digitalsage.cloud/privkey.pem ]]; then
  install -m 0644 "$REMOTE_APP_DIR/deploy/digitalsage.cloud.conf" /etc/nginx/conf.d/digital-sage.conf
else
  install -m 0644 "$REMOTE_APP_DIR/deploy/digitalsage.cloud.http.conf" /etc/nginx/conf.d/digital-sage.conf
fi

systemctl daemon-reload
systemctl enable --now digital-sage
systemctl restart digital-sage
nginx -t
systemctl reload nginx

echo "==> Local health"
healthy=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if curl -fsS http://127.0.0.1:8103/health; then
    healthy=1
    break
  fi
  sleep 2
done

if [[ "$healthy" -ne 1 ]]; then
  echo "Digital Sage failed health check on remote host" >&2
  exit 1
fi
REMOTE

echo
echo "Deploy complete."
echo "HTTP: http://digitalsage.cloud"
echo "HTTP: http://www.digitalsage.cloud"
echo
echo "If you want HTTPS next, run certbot or install your existing certificate after the app is confirmed healthy."
