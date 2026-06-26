import { useNavigate } from 'react-router-dom'

const BADGE_COLOR = {
  easy: '#22c55e', medium: '#f59e0b', hard: '#ef4444',
  expert: '#8b5cf6', master: '#ec4899'
}
const TYPE_ICON = { algorithm: '⚡', interactive: '🎨', webapp: '🌐' }

export default function ProblemCard({ problem }) {
  const nav = useNavigate()
  return (
    <div
      onClick={() => nav(`/problem/${problem.id}`)}
      style={{
        border: '1px solid #e5e7eb', borderRadius: 8, padding: 16,
        cursor: 'pointer', background: '#fff',
        transition: 'box-shadow .15s'
      }}
      onMouseEnter={e => e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,.12)'}
      onMouseLeave={e => e.currentTarget.style.boxShadow = ''}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{
          background: BADGE_COLOR[problem.difficulty], color: '#fff',
          padding: '2px 8px', borderRadius: 4, fontSize: 12, fontWeight: 600
        }}>
          {problem.difficulty[0].toUpperCase() + problem.difficulty.slice(1)}
        </span>
        <span style={{ color: '#6b7280', fontSize: 13 }}>
          {TYPE_ICON[problem.type]} {problem.type}
        </span>
      </div>
      <h3 style={{ margin: '0 0 6px', fontSize: 16 }}>{problem.title}</h3>
      <p style={{ color: '#6b7280', fontSize: 13, margin: 0, lineHeight: 1.4 }}>
        {problem.description.slice(0, 100)}{problem.description.length > 100 ? '…' : ''}
      </p>
    </div>
  )
}
