import sqlite3
import json
import time
from scanner import config


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS candidates (
                token_address     TEXT PRIMARY KEY,
                symbol            TEXT    DEFAULT '',
                chain             TEXT    DEFAULT '',
                pair_address      TEXT    DEFAULT '',
                pair_url          TEXT    DEFAULT '',
                first_seen        INTEGER DEFAULT 0,
                last_seen         INTEGER DEFAULT 0,
                price_usd         REAL    DEFAULT 0,
                liquidity_usd     REAL    DEFAULT 0,
                volume_24h        REAL    DEFAULT 0,
                vol_liq_ratio     REAL    DEFAULT 0,
                price_change_1h   REAL    DEFAULT 0,
                price_change_24h  REAL    DEFAULT 0,
                txns_24h          INTEGER DEFAULT 0,
                age_hours         REAL,
                mint_revoked      INTEGER DEFAULT 0,
                freeze_revoked    INTEGER DEFAULT 0,
                top10_holders_pct REAL    DEFAULT 100,
                is_honeypot       INTEGER DEFAULT 0,
                lp_locked         INTEGER DEFAULT 0,
                rugcheck_score    INTEGER DEFAULT 0,
                risks             TEXT    DEFAULT '[]',
                last_score        INTEGER DEFAULT 0,
                source            TEXT    DEFAULT ''
            )
        """)
        # Migration : ajoute les colonnes manquantes si DB existante
        existing = {row[1] for row in conn.execute("PRAGMA table_info(candidates)")}
        new_cols = {
            "pair_address": 'TEXT DEFAULT ""',
            "last_seen": "INTEGER DEFAULT 0",
            "price_usd": "REAL DEFAULT 0",
            "liquidity_usd": "REAL DEFAULT 0",
            "volume_24h": "REAL DEFAULT 0",
            "vol_liq_ratio": "REAL DEFAULT 0",
            "price_change_1h": "REAL DEFAULT 0",
            "price_change_24h": "REAL DEFAULT 0",
            "txns_24h": "INTEGER DEFAULT 0",
            "age_hours": "REAL",
            "mint_revoked": "INTEGER DEFAULT 0",
            "freeze_revoked": "INTEGER DEFAULT 0",
            "top10_holders_pct": "REAL DEFAULT 100",
            "is_honeypot": "INTEGER DEFAULT 0",
            "lp_locked": "INTEGER DEFAULT 0",
            "rugcheck_score": "INTEGER DEFAULT 0",
            "risks": 'TEXT DEFAULT "[]"',
            "source": 'TEXT DEFAULT ""',
        }
        for col, typedef in new_cols.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE candidates ADD COLUMN {col} {typedef}")


def is_known(token_address: str) -> bool:
    with _conn() as conn:
        return conn.execute(
            "SELECT 1 FROM candidates WHERE token_address = ?", (token_address,)
        ).fetchone() is not None


def save(pair, sec, score: int, source: str = "") -> None:
    now = int(time.time())
    with _conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO candidates (token_address, first_seen) VALUES (?, ?)",
            (pair.token_address, now),
        )
        conn.execute("""
            UPDATE candidates SET
                symbol=?, chain=?, pair_address=?, pair_url=?,
                last_seen=?,
                price_usd=?, liquidity_usd=?, volume_24h=?, vol_liq_ratio=?,
                price_change_1h=?, price_change_24h=?, txns_24h=?, age_hours=?,
                mint_revoked=?, freeze_revoked=?, top10_holders_pct=?,
                is_honeypot=?, lp_locked=?, rugcheck_score=?, risks=?,
                last_score=?, source=?
            WHERE token_address=?
        """, (
            pair.symbol, pair.chain, pair.pair_address, pair.url,
            now,
            pair.price_usd, pair.liquidity_usd, pair.volume_24h, pair.vol_liq_ratio,
            pair.price_change_1h, pair.price_change_24h, pair.txns_24h, pair.age_hours,
            int(sec.mint_revoked), int(sec.freeze_revoked), sec.top10_holders_pct,
            int(sec.is_honeypot), int(sec.lp_locked), sec.rugcheck_score,
            json.dumps(sec.risks),
            score, source,
            pair.token_address,
        ))


def all_candidates() -> list:
    with _conn() as conn:
        return conn.execute(
            "SELECT * FROM candidates ORDER BY last_score DESC"
        ).fetchall()