import { useNavigate } from 'react-router-dom'

const RANK_COLOR = {
  easy: '#56d364', medium: '#e3b341', hard: '#f0883e', expert: '#f85149',
  master: '#db61a2', challenger: '#a371f7', sovereign: '#ffd33d',
}
const TYPE_ICON = { algorithm: '⚡', interactive: '🎨', webapp: '🌐' }

export default function ProblemCard({ problem }) {
  const nav = useNavigate()
  const desc = problem.description.slice(0, 100) + (problem.description.length > 100 ? '…' : '')
  return (
    <button className="card" onClick={() => nav(`/problem/${problem.id}`)}>
      <div className="card__top">
        <span className="rank" style={{ '--rank': RANK_COLOR[problem.difficulty] }}>
          {problem.difficulty}
        </span>
        <span className="card__type">{TYPE_ICON[problem.type]} {problem.type}</span>
      </div>
      <span className="card__id">{problem.id}</span>
      <h3 className="card__title">{problem.title}</h3>
      <p className="card__desc">{desc}</p>
      <span className="card__open">open →</span>
    </button>
  )
}
