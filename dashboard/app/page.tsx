import { getCandidates } from '@/lib/db'
import TokenDashboard from './components/TokenDashboard'

export const dynamic = 'force-dynamic'
export const revalidate = 0

export default function Home() {
  const candidates = getCandidates()
  return <TokenDashboard initialData={candidates} />
}
