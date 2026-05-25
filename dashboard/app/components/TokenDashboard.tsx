'use client'

import { useState, useMemo, useCallback, useEffect } from 'react'
import type { Candidate } from '@/lib/types'

// ── Formatters ────────────────────────────────────────────────────────────────

const fmtUsd = (n: number) => {
  if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
  if (n >= 1_000) return `$${(n / 1_000).toFixed(0)}K`
  return `$${n.toFixed(0)}`
}

const fmtAge = (h: number | null) => {
  if (h === null || h === 0) return '—'
  if (h < 24) return `${h.toFixed(0)}h`
  return `${(h / 24).toFixed(1)}j`
}

const fmtPct = (n: number) => `${n > 0 ? '+' : ''}${n.toFixed(1)}%`

const timeAgo = (ts: number) => {
  if (!ts) return '—'
  const d = Math.floor(Date.now() / 1000 - ts)
  if (d < 60) return 'à l\'instant'
  if (d < 3600) return `${Math.floor(d / 60)}m`
  if (d < 86400) return `${Math.floor(d / 3600)}h`
  return `${Math.floor(d / 86400)}j`
}

const tier = (s: number) => (s >= 60 ? 'green' : s >= 35 ? 'amber' : 'red')

const SOURCE_STYLES: Record<string, string> = {
  'Pump.fun':      'bg-purple-950 text-purple-400 border-purple-800',
  'Raydium AMM':   'bg-blue-950 text-blue-400 border-blue-800',
  'Orca Whirlpool':'bg-teal-950 text-teal-400 border-teal-800',
  'GeckoTerminal': 'bg-slate-900 text-slate-400 border-slate-700',
  'DexScreener':   'bg-slate-900 text-slate-400 border-slate-700',
}

const sourceBadge = (src: string) => {
  const style = SOURCE_STYLES[src] ?? 'bg-slate-900 text-slate-400 border-slate-700'
  const label = src === 'Orca Whirlpool' ? 'Orca' : src === 'Raydium AMM' ? 'Raydium' : src
  return <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium border ${style}`}>{label}</span>
}

const T = {
  green: {
    strip: 'bg-emerald-500',
    badge: 'bg-emerald-950 text-emerald-400 border-emerald-800',
    row: 'hover:bg-emerald-950/10',
  },
  amber: {
    strip: 'bg-amber-500',
    badge: 'bg-amber-950 text-amber-400 border-amber-800',
    row: 'hover:bg-amber-950/10',
  },
  red: {
    strip: 'bg-red-900',
    badge: 'bg-red-950/60 text-red-500 border-red-900',
    row: 'hover:bg-red-950/10',
  },
}

type SortKey =
  | 'last_score' | 'liquidity_usd' | 'volume_24h' | 'vol_liq_ratio'
  | 'txns_24h' | 'age_hours' | 'price_change_24h' | 'top10_holders_pct' | 'first_seen'

interface Filters {
  search: string
  minLiq: number
  minVol: number
  minScore: number
  maxTop10: number
  hideRed: boolean
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function TokenDashboard({ initialData }: { initialData: Candidate[] }) {
  const [data, setData] = useState<Candidate[]>(initialData)
  const [loading, setLoading] = useState(false)
  const [lastUpdate, setLastUpdate] = useState(Date.now())
  const [sortKey, setSortKey] = useState<SortKey>('last_score')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [filters, setFilters] = useState<Filters>({
    search: '', minLiq: 0, minVol: 0, minScore: 0, maxTop10: 100, hideRed: false,
  })

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/candidates')
      if (res.ok) { setData(await res.json()); setLastUpdate(Date.now()) }
    } finally { setLoading(false) }
  }, [])

  useEffect(() => {
    const id = setInterval(refresh, 60_000)
    return () => clearInterval(id)
  }, [refresh])

  const handleSort = (k: SortKey) => {
    if (sortKey === k) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortKey(k); setSortDir('desc') }
  }

  const setF = (k: keyof Filters, v: unknown) => setFilters((f) => ({ ...f, [k]: v }))

  const rows = useMemo(() => {
    return data
      .filter((c) => {
        if (filters.search) {
          const q = filters.search.toLowerCase()
          if (!c.symbol.toLowerCase().includes(q) && !c.token_address.toLowerCase().includes(q))
            return false
        }
        if (c.liquidity_usd < filters.minLiq) return false
        if (c.volume_24h < filters.minVol) return false
        if (c.last_score < filters.minScore) return false
        if (c.top10_holders_pct > filters.maxTop10) return false
        if (filters.hideRed && tier(c.last_score) === 'red') return false
        return true
      })
      .sort((a, b) => {
        const av = (a[sortKey] ?? 0) as number
        const bv = (b[sortKey] ?? 0) as number
        return sortDir === 'asc' ? av - bv : bv - av
      })
  }, [data, filters, sortKey, sortDir])

  const stats = useMemo(() => ({
    total: rows.length,
    avgScore: rows.length ? Math.round(rows.reduce((s, c) => s + c.last_score, 0) / rows.length) : 0,
    safe: rows.filter((c) => c.mint_revoked && !c.is_honeypot && c.top10_holders_pct < 30).length,
    best: rows[0]?.symbol ?? '—',
  }), [rows])

  // ── Column header
  const Th = ({ label, sk, hint }: { label: string; sk?: SortKey; hint?: string }) => (
    <th
      title={hint}
      onClick={() => sk && handleSort(sk)}
      className={`px-3 py-3 text-left text-[11px] font-medium text-slate-500 uppercase tracking-wider whitespace-nowrap select-none ${sk ? 'cursor-pointer hover:text-slate-300 transition-colors' : ''}`}
    >
      {label}
      {sortKey === sk && (
        <span className="ml-1 text-indigo-400">{sortDir === 'desc' ? '↓' : '↑'}</span>
      )}
    </th>
  )

  return (
    <div className="min-h-screen bg-[#07070f] text-slate-200 font-sans">

      {/* ── Header ── */}
      <header className="sticky top-0 z-10 border-b border-[#151525] bg-[#07070f]/90 backdrop-blur px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="font-semibold text-white tracking-tight text-sm">CRYPTOSION</span>
          <span className="text-slate-600 text-xs">/ scanner</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-600 text-xs">mis à jour {timeAgo(lastUpdate / 1000)}</span>
          <button
            onClick={refresh}
            disabled={loading}
            className="px-3 py-1.5 text-xs bg-[#0d0d1a] border border-[#1a1a2e] rounded text-slate-400 hover:text-white hover:border-indigo-500/40 transition-all disabled:opacity-40 font-medium"
          >
            {loading ? '···' : '↻ Refresh'}
          </button>
        </div>
      </header>

      <div className="p-5 space-y-4">

        {/* ── Stats ── */}
        <div className="grid grid-cols-4 gap-3">
          {[
            { label: 'Candidats', val: stats.total, sub: 'après filtres actifs' },
            { label: 'Score moyen', val: stats.avgScore, sub: '/ 100' },
            { label: 'Sécurité ✓', val: stats.safe, sub: 'mint + no honey + top10 < 30%' },
            { label: 'Top token', val: stats.best, sub: 'meilleur score' },
          ].map((s) => (
            <div key={s.label} className="bg-[#0d0d1a] border border-[#151525] rounded-lg p-4">
              <div className="text-[10px] font-medium text-slate-600 uppercase tracking-wider mb-1">{s.label}</div>
              <div className="text-xl font-semibold text-white font-mono">{s.val}</div>
              <div className="text-[11px] text-slate-600 mt-0.5">{s.sub}</div>
            </div>
          ))}
        </div>

        {/* ── Filters ── */}
        <div className="bg-[#0d0d1a] border border-[#151525] rounded-lg p-4">
          <div className="flex flex-wrap gap-x-6 gap-y-4 items-end">

            {/* Search */}
            <div className="flex-1 min-w-44">
              <label className="text-[11px] text-slate-500 block mb-1.5">Rechercher</label>
              <input
                type="text"
                placeholder="Ticker ou adresse…"
                value={filters.search}
                onChange={(e) => setF('search', e.target.value)}
                className="w-full bg-[#07070f] border border-[#1a1a2e] rounded px-3 py-1.5 text-sm text-slate-200 placeholder-slate-700 focus:outline-none focus:border-indigo-500/50 transition-colors"
              />
            </div>

            {/* Sliders */}
            {([
              { k: 'minLiq', label: 'Liq min', min: 0, max: 200000, step: 5000, fmt: (v: number) => fmtUsd(v) },
              { k: 'minVol', label: 'Vol min', min: 0, max: 500000, step: 10000, fmt: (v: number) => fmtUsd(v) },
              { k: 'minScore', label: 'Score min', min: 0, max: 100, step: 5, fmt: (v: number) => `${v}` },
              { k: 'maxTop10', label: 'Top10 max', min: 10, max: 100, step: 5, fmt: (v: number) => `${v}%` },
            ] as const).map((s) => (
              <div key={s.k} className="min-w-36">
                <label className="text-[11px] text-slate-500 block mb-1.5">
                  {s.label}:{' '}
                  <span className="text-slate-300 font-mono">{s.fmt(filters[s.k] as number)}</span>
                </label>
                <input
                  type="range"
                  min={s.min}
                  max={s.max}
                  step={s.step}
                  value={filters[s.k] as number}
                  onChange={(e) => setF(s.k, Number(e.target.value))}
                  className="w-full"
                />
              </div>
            ))}

            {/* Toggle rouge */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setF('hideRed', !filters.hideRed)}
                className={`relative inline-flex h-5 w-9 shrink-0 items-center rounded-full transition-colors ${filters.hideRed ? 'bg-indigo-600' : 'bg-[#1f1f35]'}`}
              >
                <span className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${filters.hideRed ? 'translate-x-[18px]' : 'translate-x-[3px]'}`} />
              </button>
              <span className="text-[11px] text-slate-400 whitespace-nowrap">Masquer rouges</span>
            </div>
          </div>
        </div>

        {/* ── Table ── */}
        <div className="bg-[#0d0d1a] border border-[#151525] rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#151525] bg-[#090913]">
                  <th className="w-0.5 p-0" />
                  <th className="px-3 py-3 text-[11px] font-medium text-slate-600 w-8">#</th>
                  <Th label="Token" />
                  <Th label="Score" sk="last_score" hint="Score de priorité /100" />
                  <Th label="Liquidité" sk="liquidity_usd" />
                  <Th label="Vol 24h" sk="volume_24h" />
                  <Th label="Ratio" sk="vol_liq_ratio" hint="Vol / Liq" />
                  <Th label="Txns" sk="txns_24h" />
                  <Th label="Âge" sk="age_hours" />
                  <Th label="Δ 24h" sk="price_change_24h" />
                  <Th label="Top 10" sk="top10_holders_pct" hint="% supply dans les 10 premiers wallets" />
                  <Th label="Mint" hint="Mint authority révoquée" />
                  <Th label="Honey" hint="Honeypot détecté" />
                  <Th label="Vu" sk="first_seen" />
                  <Th label="Source" />
                </tr>
              </thead>

              <tbody>
                {rows.length === 0 ? (
                  <tr>
                    <td colSpan={15} className="px-6 py-20 text-center text-slate-700 text-sm">
                      {data.length === 0
                        ? 'Aucun candidat — lance le scanner avec python -m scanner.main'
                        : 'Aucun résultat avec ces filtres'}
                    </td>
                  </tr>
                ) : (
                  rows.map((c, i) => {
                    const t = tier(c.last_score)
                    const st = T[t]
                    const top10Color =
                      c.top10_holders_pct < 20
                        ? 'text-emerald-400'
                        : c.top10_holders_pct < 40
                        ? 'text-amber-400'
                        : 'text-red-400'

                    return (
                      <tr
                        key={c.token_address}
                        className={`border-b border-[#0f0f1e] ${st.row} transition-colors group`}
                      >
                        {/* Strip couleur */}
                        <td className="w-0.5 p-0">
                          <div className={`${st.strip} w-0.5`} style={{ minHeight: 48 }} />
                        </td>

                        {/* Rang */}
                        <td className="px-3 py-3 text-slate-700 text-xs font-mono">{i + 1}</td>

                        {/* Token */}
                        <td className="px-3 py-3 min-w-40">
                          <div className="flex flex-col gap-0.5">
                            <div className="flex items-center gap-2">
                              <a
                                href={c.pair_url || '#'}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="font-medium text-white hover:text-indigo-300 transition-colors text-sm"
                              >
                                {c.symbol}
                              </a>
                              {c.lp_locked && (
                                <span className="text-amber-500 text-xs" title="LP Locked">🔒</span>
                              )}
                              <a
                                href={`https://solscan.io/token/${c.token_address}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                title="Solscan"
                                className="text-slate-700 hover:text-slate-400 text-xs opacity-0 group-hover:opacity-100 transition-all"
                              >
                                ↗
                              </a>
                            </div>
                            <span className="text-slate-700 text-[10px] font-mono">
                              {c.token_address.slice(0, 6)}…{c.token_address.slice(-4)}
                            </span>
                            {c.risks.length > 0 && (
                              <span className="text-amber-600 text-[10px]" title={c.risks.join(', ')}>
                                ⚠ {c.risks[0]}
                              </span>
                            )}
                          </div>
                        </td>

                        {/* Score */}
                        <td className="px-3 py-3">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold border ${st.badge}`}>
                            {c.last_score}
                          </span>
                        </td>

                        {/* Liquidité */}
                        <td className="px-3 py-3 text-sm font-mono text-right text-slate-300">
                          {fmtUsd(c.liquidity_usd)}
                        </td>

                        {/* Volume */}
                        <td className="px-3 py-3 text-sm font-mono text-right text-slate-300">
                          {fmtUsd(c.volume_24h)}
                        </td>

                        {/* Ratio */}
                        <td className="px-3 py-3 text-sm font-mono text-right">
                          <span
                            className={
                              c.vol_liq_ratio >= 2
                                ? 'text-emerald-400'
                                : c.vol_liq_ratio >= 0.5
                                ? 'text-slate-300'
                                : 'text-red-400'
                            }
                          >
                            {c.vol_liq_ratio.toFixed(1)}x
                          </span>
                        </td>

                        {/* Txns */}
                        <td className="px-3 py-3 text-sm font-mono text-right text-slate-400">
                          {c.txns_24h.toLocaleString('fr')}
                        </td>

                        {/* Âge */}
                        <td className="px-3 py-3 text-sm font-mono text-right text-slate-400">
                          {fmtAge(c.age_hours)}
                        </td>

                        {/* Δ 24h */}
                        <td className="px-3 py-3 text-sm font-mono text-right">
                          <span className={c.price_change_24h >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                            {fmtPct(c.price_change_24h)}
                          </span>
                        </td>

                        {/* Top 10 holders */}
                        <td className={`px-3 py-3 text-sm font-mono text-right ${top10Color}`}>
                          {c.top10_holders_pct > 0 ? `${c.top10_holders_pct.toFixed(0)}%` : '—'}
                        </td>

                        {/* Mint revoked */}
                        <td className="px-3 py-3 text-center text-sm">
                          <span className={c.mint_revoked ? 'text-emerald-400' : 'text-slate-700'}>
                            {c.mint_revoked ? '✓' : '✗'}
                          </span>
                        </td>

                        {/* Honeypot */}
                        <td className="px-3 py-3 text-center text-sm">
                          <span className={!c.is_honeypot ? 'text-emerald-400' : 'text-red-500 font-bold'}>
                            {c.is_honeypot ? '✗' : '✓'}
                          </span>
                        </td>

                        {/* Vu */}
                        <td className="px-3 py-3 text-[11px] text-slate-600 whitespace-nowrap">
                          {timeAgo(c.first_seen)}
                        </td>

                        {/* Source */}
                        <td className="px-3 py-3 whitespace-nowrap">
                          {sourceBadge(c.source || '—')}
                        </td>
                      </tr>
                    )
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Footer */}
          <div className="px-4 py-2.5 border-t border-[#151525] flex items-center justify-between text-[11px] text-slate-700">
            <span>{rows.length} token{rows.length !== 1 ? 's' : ''} affiché{rows.length !== 1 ? 's' : ''} / {data.length} en base</span>
            <span>Refresh auto · 60s · scanner.db</span>
          </div>
        </div>

      </div>
    </div>
  )
}
