function scoreColor(score) {
  if (score === 100) return 'var(--pass)'
  if (score >= 50) return 'var(--warn)'
  return 'var(--fail)'
}

export default function ResultPanel({ result }) {
  if (!result) return null
  const { score, passed, total, results, error } = result
  const color = scoreColor(score)

  return (
    <section className="result" style={{ '--score': color }}>
      <div className="result__bar">{error ? 'run failed' : 'run complete'} · {total} {total === 1 ? 'case' : 'cases'}</div>

      <div className="result__head">
        <div className="score">{score}<small>/100</small></div>
        <div className="score-meta"><b>{passed}/{total}</b> {total === 1 ? 'case' : 'cases'} passed</div>
      </div>
      <div className="meter"><div className="meter__fill" style={{ width: `${score}%` }} /></div>

      {error && <pre className="stderr">{error}</pre>}

      {results.length > 0 && (
        <div className="cases">
          {results.map(r => (
            <div className={r.passed ? 'case case--pass' : 'case case--fail'} key={r.case}>
              <span className={r.passed ? 'badge badge--pass' : 'badge badge--fail'}>
                {r.passed ? 'PASS' : 'FAIL'}
              </span>
              <span className="case__name">case {r.case}</span>
              {!r.passed && (
                <span className="case__diff">
                  got <code>{r.output}</code><span className="arrow">→</span>expected <code>{r.expected}</code>
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
