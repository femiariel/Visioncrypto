import { NextResponse } from 'next/server'
import { getCandidates } from '@/lib/db'

export const dynamic = 'force-dynamic'

export async function GET() {
  return NextResponse.json(getCandidates())
}