import time
import httpx
from dataclasses import dataclass
from typing import Optional

DEXSCREENER_BASE = "https://api.dexscreener.com"
GECKOTERMINAL_BASE = "https://api.geckoterminal.com/api/v2"

_client = httpx.Client(timeout=10, headers={"User-Agent": "cryptosion/1.0"})


@dataclass
class Pair:
    chain: str
    dex: str
    pair_address: str
    token_address: str
    symbol: str
    price_usd: float
    liquidity_usd: float
    volume_24h: float
    price_change_1h: float
    price_change_24h: float
    txns_24h: int
    pair_created_at: Optional[int]  # timestamp Unix en ms
    url: str

    @property
    def age_hours(self) -> Optional[float]:
        if not self.pair_created_at:
            return None
        return (time.time() * 1000 - self.pair_created_at) / 3_600_000

    @property
    def vol_liq_ratio(self) -> float:
        return self.volume_24h / self.liquidity_usd if self.liquidity_usd > 0 else 0


def _get(url: str):
    r = _client.get(url)
    r.raise_for_status()
    return r.json()


# ─── DexScreener ────────────────────────────────────────────────────────────

def _dex_addresses(chain: str) -> dict:
    addresses = {}
    # Featured/boosted tokens
    for endpoint in ["token-profiles/latest/v1", "token-boosts/latest/v1"]:
        try:
            data = _get(f"{DEXSCREENER_BASE}/{endpoint}")
            if isinstance(data, list):
                for item in data:
                    if item.get("chainId") == chain:
                        addr = item.get("tokenAddress")
                        if addr and addr not in addresses:
                            addresses[addr] = "DexScreener"
        except Exception as e:
            print(f"  [WARN] dexscreener/{endpoint}: {e}")
    return addresses


def fetch_pairs_batch(chain: str, addresses: list) -> dict:
    """Fetch pairs for up to 30 addresses in one DexScreener call.
    Returns {token_address: [Pair, ...]}."""
    if not addresses:
        return {}
    joined = ",".join(addresses[:30])
    result: dict = {}
    try:
        data = _get(f"{DEXSCREENER_BASE}/tokens/v1/{chain}/{joined}")
        pairs = data if isinstance(data, list) else []
        for raw in pairs:
            p = _parse_dex_pair(raw)
            if p:
                result.setdefault(p.token_address, []).append(p)
    except Exception as e:
        print(f"  [WARN] fetch_pairs_batch: {e}")
    return result


def fetch_pairs(chain: str, token_address: str) -> list:
    """Paires de trading pour un token donné (via DexScreener)."""
    return fetch_pairs_batch(chain, [token_address]).get(token_address, [])


def _parse_dex_pair(p: dict) -> Optional[Pair]:
    try:
        liq = float((p.get("liquidity") or {}).get("usd") or 0)
        vol = float((p.get("volume") or {}).get("h24") or 0)
        txns = p.get("txns", {}).get("h24", {})
        return Pair(
            chain=p.get("chainId", ""),
            dex=p.get("dexId", ""),
            pair_address=p.get("pairAddress", ""),
            token_address=p["baseToken"]["address"],
            symbol=p["baseToken"]["symbol"],
            price_usd=float(p.get("priceUsd") or 0),
            liquidity_usd=liq,
            volume_24h=vol,
            price_change_1h=float((p.get("priceChange") or {}).get("h1") or 0),
            price_change_24h=float((p.get("priceChange") or {}).get("h24") or 0),
            txns_24h=txns.get("buys", 0) + txns.get("sells", 0),
            pair_created_at=p.get("pairCreatedAt"),
            url=p.get("url", ""),
        )
    except Exception:
        return None


# ─── GeckoTerminal ───────────────────────────────────────────────────────────

GECKO_MAX_PAGES = {"new_pools": 5, "trending_pools": 5}

def _gecko_addresses(chain: str = "solana") -> dict:
    addresses = {}
    network = "solana" if chain == "solana" else chain

    for source, max_pages in GECKO_MAX_PAGES.items():
        for page in range(1, max_pages + 1):
            try:
                data = _get(f"{GECKOTERMINAL_BASE}/networks/{network}/{source}?page={page}")
                pools = data.get("data", [])
                if not pools:
                    break
                for pool in pools:
                    tid = pool.get("relationships", {}).get("base_token", {}).get("data", {}).get("id", "")
                    if "_" in tid:
                        addr = tid.split("_", 1)[1]
                        if addr not in addresses:
                            addresses[addr] = "GeckoTerminal"
                time.sleep(6)
            except Exception as e:
                print(f"  [WARN] GeckoTerminal {source} p{page}: {e}")
                time.sleep(10)  # backoff après 429
                break

    print(f"  GeckoTerminal: {len(addresses)} adresses")
    return addresses


# ─── Helius (Pump.fun new tokens) ─────────────────────────────────────────────

HELIUS_BASE = "https://api.helius.xyz/v0"

# Programmes Solana surveillés — (nom, adresse, type de tx à filtrer)
HELIUS_PROGRAMS = [
    ("Pump.fun",       "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P", "CREATE"),
    ("Raydium AMM",    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8", None),
    ("Orca Whirlpool", "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",  None),
]


def _fetch_program_mints(api_key: str, program: str, source_name: str, tx_type: str = None, pages: int = 2) -> dict:
    """Pagine les transactions d'un programme Solana et retourne {mint: source}."""
    addresses = {}
    before = None

    for page in range(pages):
        try:
            params = {"api-key": api_key, "limit": 100}
            if tx_type:
                params["type"] = tx_type
            if before:
                params["before"] = before

            r = httpx.get(
                f"{HELIUS_BASE}/addresses/{program}/transactions",
                params=params,
                timeout=30,
            )

            if r.status_code != 200:
                break

            txns = r.json()
            if not txns:
                break

            for tx in txns:
                for transfer in tx.get("tokenTransfers", []):
                    mint = transfer.get("mint")
                    if mint and mint not in addresses:
                        addresses[mint] = source_name

            before = txns[-1].get("signature")
            if not before:
                break

            time.sleep(0.2)

        except Exception as e:
            print(f"  [WARN] Helius {source_name} p{page+1}: {e}")
            break

    return addresses


def _helius_addresses(api_key: str) -> dict:
    if not api_key:
        return {}

    all_mints = {}
    for name, program, tx_type in HELIUS_PROGRAMS:
        mints = _fetch_program_mints(api_key, program, name, tx_type, pages=2)
        print(f"  Helius {name}: {len(mints)} mints")
        # Ne pas écraser une source déjà enregistrée
        for addr, src in mints.items():
            if addr not in all_mints:
                all_mints[addr] = src

    print(f"  Helius total: {len(all_mints)} adresses uniques")
    return all_mints


# ─── Point d'entrée principal ─────────────────────────────────────────────────

def fetch_token_addresses(chain: str) -> dict:
    """
    Collecte les adresses depuis DexScreener + GeckoTerminal + Helius.
    Retourne un dict {token_address: source_name}.
    Priorité : Helius (blockchain) > GeckoTerminal > DexScreener.
    """
    from scanner import config

    dex    = _dex_addresses(chain)
    print(f"  DexScreener: {len(dex)} adresses")

    gecko  = _gecko_addresses(chain)
    helius = _helius_addresses(config.HELIUS_API_KEY) if chain == "solana" else {}

    # Merge avec priorité Helius > Gecko > Dex
    merged = {**dex, **gecko, **helius}
    print(f"  Total unique: {len(merged)}")
    return merged
