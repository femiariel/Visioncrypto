import httpx
from scanner import config
from scanner.fetcher import Pair
from scanner.enricher import SecurityData


def _format(pair: Pair, sec: SecurityData, score: int) -> str:
    age = pair.age_hours
    age_str = f"{age:.0f}h" if age is not None else "?"

    flags = []
    if sec.mint_revoked:   flags.append("Mint révoqué")
    if sec.freeze_revoked: flags.append("Freeze révoqué")
    if sec.lp_locked:      flags.append("LP locked")
    if sec.risks:          flags.append(f"Risques: {', '.join(sec.risks[:2])}")
    if not sec.fetched:    flags.append("Sécurité non vérifiée")

    sec_str = " | ".join(flags) if flags else "—"

    return (
        f"*{pair.symbol}* — {pair.chain.upper()} | Score {score}/100\n\n"
        f"Liq     : ${pair.liquidity_usd:,.0f}\n"
        f"Vol 24h : ${pair.volume_24h:,.0f} ({pair.vol_liq_ratio:.1f}x liq)\n"
        f"1h/24h  : {pair.price_change_1h:+.1f}% / {pair.price_change_24h:+.1f}%\n"
        f"Txns    : {pair.txns_24h}\n"
        f"Age     : {age_str}\n\n"
        f"Securite: {sec_str}\n\n"
        f"[DexScreener]({pair.url})"
    )


def send(pair: Pair, sec: SecurityData, score: int) -> None:
    text = _format(pair, sec, score)

    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print(f"  [DRY RUN] {pair.symbol} | score={score} | liq=${pair.liquidity_usd:,.0f}")
        return

    try:
        httpx.post(
            f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": False,
            },
            timeout=10,
        )
    except Exception as e:
        print(f"  [WARN] Telegram: {e}")
