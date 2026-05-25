import time
import json
from pathlib import Path
from scanner import config, database, notifier
from scanner.fetcher import fetch_pairs_batch, _dex_addresses, _gecko_addresses, _helius_addresses
from scanner.enricher import fetch_security
from scanner.scorer import calculate_score

EXPORT_PATH = Path(__file__).parent.parent / "scanner_data.json"


def export_json() -> None:
    """Exporte tous les candidats en JSON pour le dashboard."""
    rows = database.all_candidates()
    data = []
    for r in rows:
        d = dict(r)
        d["mint_revoked"] = bool(d.get("mint_revoked"))
        d["freeze_revoked"] = bool(d.get("freeze_revoked"))
        d["is_honeypot"] = bool(d.get("is_honeypot"))
        d["lp_locked"] = bool(d.get("lp_locked"))
        d["risks"] = json.loads(d.get("risks") or "[]")
        data.append(d)
    EXPORT_PATH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


_last_helius_scan: float = 0


def run_scan() -> None:
    global _last_helius_scan
    print(f"[{time.strftime('%H:%M:%S')}] Scan {config.CHAIN}...")

    # DexScreener + GeckoTerminal à chaque cycle
    dex = _dex_addresses(config.CHAIN)
    print(f"  DexScreener: {len(dex)} adresses")
    gecko = _gecko_addresses(config.CHAIN)

    # Helius toutes les HELIUS_SCAN_INTERVAL_MINUTES
    now = time.time()
    helius_due = (now - _last_helius_scan) >= config.HELIUS_SCAN_INTERVAL_MINUTES * 60
    if config.CHAIN == "solana" and helius_due:
        helius = _helius_addresses(config.HELIUS_API_KEY)
        _last_helius_scan = now
    else:
        helius = {}

    address_map = {**dex, **gecko, **helius}
    print(f"  {len(address_map)} adresses collectées")

    # Batch fetch pairs — 30 adresses par appel DexScreener
    addrs = list(address_map.keys())
    all_pairs: dict = {}
    BATCH = 30
    for i in range(0, len(addrs), BATCH):
        batch = addrs[i:i + BATCH]
        result = fetch_pairs_batch(config.CHAIN, batch)
        all_pairs.update(result)
        if i + BATCH < len(addrs):
            time.sleep(0.3)

    print(f"  {len(all_pairs)} tokens avec paires")

    candidates = []
    f_liq = f_vol = f_ratio = f_txns = f_age = f_price = f_known = f_honey = f_top10 = 0

    for addr, pairs_list in all_pairs.items():
        source = address_map.get(addr, "")

        # Paire avec le plus de volume pour ce token
        pair = max(pairs_list, key=lambda p: p.volume_24h)

        # --- Filtres éliminatoires (sans appel externe) ---
        if pair.liquidity_usd < config.LIQUIDITY_MIN_USD:
            f_liq += 1; continue
        if pair.volume_24h < config.VOLUME_24H_MIN_USD:
            f_vol += 1; continue
        if pair.vol_liq_ratio < config.VOLUME_LIQUIDITY_RATIO_MIN:
            f_ratio += 1; continue
        if pair.txns_24h < config.TXNS_24H_MIN:
            f_txns += 1; continue
        if pair.age_hours is not None:
            if pair.age_hours < config.AGE_MIN_HOURS or pair.age_hours > config.AGE_MAX_DAYS * 24:
                f_age += 1; continue
        if not (config.PRICE_CHANGE_24H_MIN_PCT
                <= pair.price_change_24h
                <= config.PRICE_CHANGE_24H_MAX_PCT):
            f_price += 1; continue

        # Déjà notifié
        if database.is_known(pair.token_address):
            f_known += 1; continue

        # --- Enrichissement sécurité ---
        sec = fetch_security(pair.token_address)
        time.sleep(0.5)  # respecte le rate limit RugCheck

        # --- Filtres éliminatoires sécurité ---
        if sec.is_honeypot:
            f_honey += 1; continue
        if sec.fetched and sec.top10_holders_pct > config.TOP10_HOLDERS_MAX_PCT:
            f_top10 += 1; continue

        score = calculate_score(pair, sec)
        candidates.append((pair, sec, score, source))

    candidates.sort(key=lambda x: x[2], reverse=True)
    top = candidates[:config.MAX_CANDIDATES]

    print(f"  Filtres: liq={f_liq} vol={f_vol} ratio={f_ratio} txns={f_txns} age={f_age} price={f_price} known={f_known} honey={f_honey} top10={f_top10}")
    print(f"  {len(candidates)} candidat(s) — {len(top)} à notifier")

    for pair, sec, score, source in top:
        database.save(pair, sec, score, source)
        notifier.send(pair, sec, score)
        time.sleep(1)

    export_json()


def main() -> None:
    database.init_db()
    print(f"Scanner démarré — chain={config.CHAIN}, interval={config.SCAN_INTERVAL_MINUTES}min")
    print(f"Filtres : liq>=${config.LIQUIDITY_MIN_USD:,.0f}, vol24h>=${config.VOLUME_24H_MIN_USD:,.0f}, "
          f"txns>={config.TXNS_24H_MIN}, age={config.AGE_MIN_HOURS}h-{config.AGE_MAX_DAYS}j, "
          f"change={config.PRICE_CHANGE_24H_MIN_PCT}%-{config.PRICE_CHANGE_24H_MAX_PCT}%\n")

    while True:
        try:
            run_scan()
        except Exception as e:
            print(f"[ERROR] {e}")
        print(f"  Prochain scan dans {config.SCAN_INTERVAL_MINUTES} min\n")
        time.sleep(config.SCAN_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
