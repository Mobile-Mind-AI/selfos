"use client"
import { useEffect, useState } from 'react'

type LifeArea = { id: string; name: string; color?: string | null }
type Page<T> = { total: number; items: T[] }

export default function LifeAreasPage() {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
  const [data, setData] = useState<Page<LifeArea> | null>(null)
  const [name, setName] = useState('')

  const reload = () => fetch(base + '/v1/life-areas/').then(r => r.json()).then(setData)
  useEffect(() => { reload() }, [])

  const create = async () => {
    await fetch(base + '/v1/life-areas/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }) })
    setName('')
    reload()
  }

  return (
    <main style={{ padding: 24 }}>
      <h2>Life Areas</h2>
      <div style={{ marginBottom: 12 }}>
        <input value={name} onChange={e => setName(e.target.value)} placeholder="Название" />
        <button onClick={create} disabled={!name}>Создать</button>
      </div>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </main>
  )
}

