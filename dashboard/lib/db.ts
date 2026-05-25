import fs from 'fs'
import path from 'path'
import type { Candidate } from './types'

const DATA_PATH = process.env.DATA_PATH
  ? path.resolve(process.cwd(), process.env.DATA_PATH)
  : path.join(process.cwd(), '..', 'scanner_data.json')

export function getCandidates(): Candidate[] {
  try {
    if (!fs.existsSync(DATA_PATH)) return []
    const raw = fs.readFileSync(DATA_PATH, 'utf-8')
    return JSON.parse(raw) as Candidate[]
  } catch {
    return []
  }
}
