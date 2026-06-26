export default function ResultPanel({ result }) {
  if (!result) return null
  const { score, passed, total, results, error } = result
  return (
    <div style={{ marginTop: 24, padding: 16, border: '1px solid #e5e7eb', borderRadius: 8, background: '#fff' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 8 }}>
        <h2 style={{ margin: 0, fontSize: 28, color: score === 100 ? '#16a34a' : score >= 50 ? '#d97706' : '#dc2626' }}>
          {score}/100
        </h2>
        <span style={{ color: '#6b7280' }}>{passed}/{total} tests passed</span>
      </div>

      {error && (
        <pre style={{
          background: '#fee2e2', color: '#dc2626', padding: 12,
          borderRadius: 4, fontSize: 12, overflowX: 'auto', marginBottom: 12
        }}>
          {error}
        </pre>
      )}

      <div>
        {results.map(r => (
          <div key={r.case} style={{
            display: 'flex', alignItems: 'flex-start', gap: 8,
            padding: '8px 12px', marginBottom: 4, borderRadius: 4,
            background: r.passed ? '#dcfce7' : '#fee2e2'
          }}>
            <span style={{ fontWeight: 700, color: r.passed ? '#16a34a' : '#dc2626' }}>
              {r.passed ? '✓' : '✗'}
            </span>
            <span style={{ color: '#374151' }}>Case {r.case}</span>
            {!r.passed && (
              <span style={{ color: '#6b7280', fontSize: 12, marginLeft: 4 }}>
                got: <code>{r.output}</code> · expected: <code>{r.expected}</code>
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
