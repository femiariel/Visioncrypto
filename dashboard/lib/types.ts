export interface Candidate {
  token_address: string
  symbol: string
  chain: string
  pair_address: string
  pair_url: string
  first_seen: number
  last_seen: number
  price_usd: number
  liquidity_usd: number
  volume_24h: number
  vol_liq_ratio: number
  price_change_1h: number
  price_change_24h: number
  txns_24h: number
  age_hours: number | null
  mint_revoked: boolean
  freeze_revoked: boolean
  top10_holders_pct: number
  is_honeypot: boolean
  lp_locked: boolean
  rugcheck_score: number
  risks: string[]
  last_score: number
  source: string
}
