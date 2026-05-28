#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# ── Vérifie que .env existe ──────────────────────────────────────────────────
if [ ! -f .env ]; then
  echo "[ERROR] .env manquant — copie .env.example et remplis les clés"
  exit 1
fi

# ── Python venv ──────────────────────────────────────────────────────────────
if [ ! -d .venv ]; then
  echo "[0/3] Création du venv Python..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -q

# ── Dashboard ────────────────────────────────────────────────────────────────
echo "[1/3] Build + lancement du dashboard..."
cd dashboard
npm install --silent
npm run build
screen -S dashboard -X quit 2>/dev/null || true
screen -dmS dashboard bash -c "cd $PROJECT_DIR/dashboard && npm start -- --port 3333"
cd "$PROJECT_DIR"

# ── Nginx (proxy port 80 → 3333) ─────────────────────────────────────────────
echo "[2/3] Configuration nginx..."
apt-get install -y -q nginx 2>/dev/null || true

cat > /etc/nginx/sites-available/cryptosion << EOF
server {
    listen 80 default_server;

    location /_next/static/ {
        alias $PROJECT_DIR/dashboard/.next/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:3333;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

ln -sf /etc/nginx/sites-available/cryptosion /etc/nginx/sites-enabled/cryptosion
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# ── Scanner Python ───────────────────────────────────────────────────────────
echo "[3/3] Lancement du scanner..."
screen -S scanner -X quit 2>/dev/null || true
screen -dmS scanner bash -c "source $PROJECT_DIR/.venv/bin/activate && cd $PROJECT_DIR && python3 -u -m scanner.main"

IP=$(hostname -I | awk '{print $1}')
echo ""
echo "  Dashboard → http://$IP"
echo "  screen -r scanner    → logs du scanner"
echo "  screen -r dashboard  → logs du dashboard"
