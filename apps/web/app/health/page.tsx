"use client"
import { useEffect, useState } from 'react'

export default function HealthPage() {
  const [data, setData] = useState<any>(null)
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  useEffect(() => {
    fetch(base + '/health').then(r => r.json()).then(setData).catch(() => setData({ error: true }))
  }, [base])
  return (
    <main style={{ padding: 24 }}>
      <h2>Health</h2>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </main>
  )
}

