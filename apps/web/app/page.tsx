import Link from 'next/link'

export default function Home() {
  return (
    <main style={{ padding: 24 }}>
      <h1>SelfOS Web (Phase 2)</h1>
      <ul>
        <li><Link href="/health">/health</Link></li>
        <li><Link href="/life-areas">/life-areas</Link></li>
      </ul>
    </main>
  )
}

