from scanner.fetcher import Pair
from scanner.enricher import SecurityData


def calculate_score(pair: Pair, sec: SecurityData) -> int:
    score = 0

    # Liquidité — 20 pts
    liq = pair.liquidity_usd
    if liq >= 200_000:   score += 20
    elif liq >= 100_000: score += 15
    elif liq >= 50_000:  score += 10
    else:                score += 5

    # Ratio volume/liquidité — 25 pts
    ratio = pair.vol_liq_ratio
    if ratio >= 5:     score += 25
    elif ratio >= 2:   score += 20
    elif ratio >= 1:   score += 15
    elif ratio >= 0.5: score += 10

    # Momentum prix dans la fourchette saine — 15 pts
    chg = pair.price_change_24h
    if 10 <= chg <= 100:   score += 15
    elif 100 < chg <= 300: score += 10
    elif 0 < chg < 10:     score += 5

    # Transactions — 10 pts
    txns = pair.txns_24h
    if txns >= 2000:   score += 10
    elif txns >= 1000: score += 8
    elif txns >= 500:  score += 5
    elif txns >= 200:  score += 3

    # Bonus sécurité — 10 pts
    if sec.mint_revoked:   score += 5
    if sec.freeze_revoked: score += 3
    if sec.lp_locked:      score += 2

    return score
