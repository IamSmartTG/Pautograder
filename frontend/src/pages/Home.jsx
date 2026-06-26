import { useState, useEffect } from 'react'
import ProblemCard from '../components/ProblemCard'

const DIFFICULTIES = ['all', 'easy', 'medium', 'hard', 'expert', 'master', 'challenger', 'sovereign']
const TYPES = ['all', 'algorithm', 'interactive', 'webapp']

function FilterBtn({ label, active, onClick }) {
  return (
    <button onClick={onClick} style={{
      padding: '4px 12px', border: 'none', borderRadius: 4, cursor: 'pointer',
      background: active ? '#3b82f6' : '#e5e7eb',
      color: active ? '#fff' : '#374151', fontWeight: active ? 600 : 400
    }}>
      {label[0].toUpperCase() + label.slice(1)}
    </button>
  )
}

export default function Home() {
  const [problems, setProblems] = useState([])
  const [diff, setDiff] = useState('all')
  const [type, setType] = useState('all')

  useEffect(() => {
    fetch('/api/problems').then(r => r.json()).then(setProblems)
  }, [])

  const visible = problems.filter(p =>
    (diff === 'all' || p.difficulty === diff) &&
    (type === 'all' || p.type === type)
  )

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24 }}>
      <h1 style={{ marginBottom: 4 }}>Pautograder</h1>
      <p style={{ color: '#6b7280', marginBottom: 20 }}>Submit your solution and get instant feedback.</p>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
        {DIFFICULTIES.map(d => <FilterBtn key={d} label={d} active={diff === d} onClick={() => setDiff(d)} />)}
        <span style={{ color: '#d1d5db', margin: '0 4px' }}>|</span>
        {TYPES.map(t => <FilterBtn key={t} label={t} active={type === t} onClick={() => setType(t)} />)}
      </div>

      {visible.length === 0 && (
        <p style={{ color: '#9ca3af' }}>No problems match these filters.</p>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {visible.map(p => <ProblemCard key={p.id} problem={p} />)}
      </div>
    </div>
  )
}
