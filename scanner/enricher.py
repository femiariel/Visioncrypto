"""
Enrichissement sécurité via RugCheck (gratuit, sans clé).
Appelé uniquement sur les tokens qui ont passé les filtres DexScreener.
"""
import httpx
from dataclasses import dataclass, field

RUGCHECK_BASE = "https://api.rugcheck.xyz/v1"
_client = httpx.Client(timeout=15, headers={"User-Agent": "cryptosion/1.0"})


@dataclass
class SecurityData:
    token_address: str
    mint_revoked: bool = False
    freeze_revoked: bool = False
    top10_holders_pct: float = 100.0
    is_honeypot: bool = False
    lp_locked: bool = False
    rugcheck_score: int = 0
    risks: list = field(default_factory=list)
    fetched: bool = False  # False = requête échouée, données non fiables


def fetch_security(token_address: str) -> SecurityData:
    sec = SecurityData(token_address=token_address)
    try:
        r = _client.get(f"{RUGCHECK_BASE}/tokens/{token_address}/report")
        if r.status_code == 429:
            print(f"  [WARN] RugCheck rate limit — {token_address[:8]}")
            return sec
        if r.status_code != 200:
            return sec

        data = r.json()
        sec.fetched = True
        sec.rugcheck_score = data.get("score", 0)

        sec.mint_revoked = data.get("mintAuthority") is None
        sec.freeze_revoked = data.get("freezeAuthority") is None

        top_holders = data.get("topHolders", [])
        if top_holders:
            raw = sum(h.get("pct", 0) for h in top_holders[:10])
            # RugCheck renvoie parfois des pcts en décimal (0.15 = 15%), parfois en entier (15)
            sec.top10_holders_pct = raw * 100 if raw <= 1.0 else raw

        risks = data.get("risks", [])
        sec.risks = [r["name"] for r in risks if r.get("level") in ("warn", "danger")]
        sec.is_honeypot = any("honeypot" in r.get("name", "").lower() for r in risks)

        for market in data.get("markets", []):
            lp = market.get("lp", {})
            if lp.get("lpLockedPct", 0) > 80:
                sec.lp_locked = True
                break

    except Exception as e:
        print(f"  [WARN] RugCheck erreur — {token_address[:8]}: {e}")

    return sec
