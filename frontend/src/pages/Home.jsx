import { useState, useEffect } from 'react'
import ProblemCard from '../components/ProblemCard'

const DIFFICULTIES = ['all', 'easy', 'medium', 'hard', 'expert', 'master', 'challenger', 'sovereign']
const TYPES = ['all', 'algorithm', 'interactive', 'webapp']

function Chip({ label, active, onClick }) {
  return (
    <button className={active ? 'chip chip--on' : 'chip'} onClick={onClick}>
      {label}
    </button>
  )
}

export default function Home() {
  const [problems, setProblems] = useState([])
  const [diff, setDiff] = useState('all')
  const [type, setType] = useState('all')

  useEffect(() => {
    fetch('/api/problems').then(r => r.json()).then(setProblems).catch(() => {})
  }, [])

  const visible = problems.filter(p =>
    (diff === 'all' || p.difficulty === diff) &&
    (type === 'all' || p.type === type)
  )

  function reset() { setDiff('all'); setType('all') }

  return (
    <main className="page">
      <p className="eyebrow">// {problems.length} problems · no account needed</p>
      <h1 className="title">Run your code. Get graded.</h1>
      <p className="lead comment">// pick a problem, submit a solution, watch it run in a sandbox</p>

      <div className="filters">
        <div className="filter-group">
          {DIFFICULTIES.map(d => <Chip key={d} label={d} active={diff === d} onClick={() => setDiff(d)} />)}
        </div>
        <span className="filter-sep" />
        <div className="filter-group">
          {TYPES.map(t => <Chip key={t} label={t} active={type === t} onClick={() => setType(t)} />)}
        </div>
      </div>

      {visible.length === 0 ? (
        <div className="empty">
          <b>No problems match these filters.</b>{' '}
          <button className="linklike" onClick={reset}>Clear filters</button>
        </div>
      ) : (
        <div className="grid">
          {visible.map(p => <ProblemCard key={p.id} problem={p} />)}
        </div>
      )}
    </main>
  )
}
