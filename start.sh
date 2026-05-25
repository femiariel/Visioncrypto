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
  echo "[0/2] Création du venv Python..."
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -r requirements.txt -q

# ── Dashboard ────────────────────────────────────────────────────────────────
echo "[1/2] Build + lancement du dashboard..."
cd dashboard
npm install --silent
npm run build
screen -dmS dashboard npm start -- --port 3333
cd "$PROJECT_DIR"
echo "  Dashboard → http://$(hostname -I | awk '{print $1}'):8080/cryptovision"

# ── Scanner Python ───────────────────────────────────────────────────────────
echo "[2/2] Lancement du scanner..."
screen -dmS scanner bash -c "source $PROJECT_DIR/.venv/bin/activate && python3 -u -m scanner.main"

echo ""
echo "  screen -r scanner    → logs du scanner"
echo "  screen -r dashboard  → logs du dashboard"
echo "  screen -ls           → liste des process"
