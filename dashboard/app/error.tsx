'use client'

export default function Error({ error }: { error: Error }) {
  return (
    <div style={{ background: '#07070f', color: '#e2e8f0', padding: 24, minHeight: '100vh', fontFamily: 'monospace' }}>
      <h2 style={{ color: '#f87171', marginBottom: 12 }}>Erreur client</h2>
      <pre style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>{error?.message}</pre>
      <pre style={{ whiteSpace: 'pre-wrap', fontSize: 11, color: '#64748b', marginTop: 12 }}>{error?.stack}</pre>
    </div>
  )
}
