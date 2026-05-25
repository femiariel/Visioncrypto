#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# ── Vérifie que .env existe ──────────────────────────────────────────────────
if [ ! -f .env ]; then
  echo "[ERROR] .env manquant — copie .env.example et remplis les clés"
  exit 1
fi

# ── Dashboard ────────────────────────────────────────────────────────────────
echo "[1/2] Build + lancement du dashboard..."
cd dashboard
npm install --silent
npm run build
screen -dmS dashboard npm start -- --port 8080
cd "$PROJECT_DIR"
echo "  Dashboard lancé → http://$(hostname -I | awk '{print $1}'):8080/cryptovision"

# ── Scanner Python ───────────────────────────────────────────────────────────
echo "[2/2] Lancement du scanner..."
pip install -r requirements.txt -q
screen -dmS scanner python3 -u -m scanner.main

echo ""
echo "  screen -r scanner    → logs du scanner"
echo "  screen -r dashboard  → logs du dashboard"
echo "  screen -ls           → liste des process"
