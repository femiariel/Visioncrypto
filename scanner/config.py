import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# --- Scan ---
CHAIN                       = os.getenv("CHAIN", "solana")
SCAN_INTERVAL_MINUTES       = int(os.getenv("SCAN_INTERVAL_MINUTES", "5"))
MAX_CANDIDATES              = int(os.getenv("MAX_CANDIDATES", "15"))

# --- Liquidité ---
LIQUIDITY_MIN_USD           = float(os.getenv("LIQUIDITY_MIN_USD", "30000"))

# --- Volume ---
VOLUME_24H_MIN_USD          = float(os.getenv("VOLUME_24H_MIN_USD", "50000"))
VOLUME_LIQUIDITY_RATIO_MIN  = float(os.getenv("VOLUME_LIQUIDITY_RATIO_MIN", "0.5"))
TXNS_24H_MIN                = int(os.getenv("TXNS_24H_MIN", "200"))

# --- Âge de la paire ---
AGE_MIN_HOURS               = int(os.getenv("AGE_MIN_HOURS", "2"))
AGE_MAX_DAYS                = int(os.getenv("AGE_MAX_DAYS", "30"))

# --- Momentum ---
PRICE_CHANGE_24H_MIN_PCT    = float(os.getenv("PRICE_CHANGE_24H_MIN_PCT", "10"))
PRICE_CHANGE_24H_MAX_PCT    = float(os.getenv("PRICE_CHANGE_24H_MAX_PCT", "300"))

# --- Sécurité ---
TOP10_HOLDERS_MAX_PCT       = float(os.getenv("TOP10_HOLDERS_MAX_PCT", "40"))
SELL_FEE_MAX_PCT            = float(os.getenv("SELL_FEE_MAX_PCT", "10"))

# --- Helius ---
HELIUS_API_KEY              = os.getenv("HELIUS_API_KEY", "")
HELIUS_SCAN_INTERVAL_MINUTES = int(os.getenv("HELIUS_SCAN_INTERVAL_MINUTES", "30"))
HELIUS_PAGES                = int(os.getenv("HELIUS_PAGES", "2"))

# --- Telegram ---
TELEGRAM_BOT_TOKEN          = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID            = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Base de données ---
DB_PATH                     = str(Path(__file__).parent.parent / "scanner.db")
