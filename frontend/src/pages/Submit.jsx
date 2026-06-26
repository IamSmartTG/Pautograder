import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import ResultPanel from '../components/ResultPanel'

export default function Submit() {
  const { id } = useParams()
  const nav = useNavigate()
  const [problem, setProblem] = useState(null)
  const [tab, setTab] = useState('paste')
  const [code, setCode] = useState('')
  const [file, setFile] = useState(null)
  const [fileError, setFileError] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const fileRef = useRef()

  useEffect(() => {
    fetch(`/api/problems/${id}`)
      .then(r => r.json())
      .then(data => {
        if (data.detail) { nav('/'); return; }
        setProblem(data)
      })
      .catch(() => nav('/'))
  }, [id])

  function handleFileChange(e) {
    const f = e.target.files[0]
    if (!f) return
    if (f.size > 10 * 1024 * 1024) {
      setFileError('File exceeds 10MB limit')
      setFile(null)
      return
    }
    setFileError(null)
    setFile(f)
  }

  async function handleSubmit() {
    setLoading(true)
    setResult(null)
    const form = new FormData()
    if (tab === 'paste') form.append('code', code)
    else form.append('file', file)

    try {
      const res = await fetch(`/api/submit/${id}`, { method: 'POST', body: form })
      const data = await res.json()
      setResult(res.ok ? data : { score: 0, passed: 0, total: 0, results: [], error: data.detail ?? 'Server error' })
    } finally {
      setLoading(false)
    }
  }

  if (!problem) return <div style={{ padding: 24 }}>Loading…</div>

  const canSubmit = !loading && (tab === 'paste' ? code.trim() : !!file)
  const TabBtn = ({ t, label }) => (
    <button onClick={() => setTab(t)} style={{
      padding: '6px 16px', border: 'none', borderRadius: 4, cursor: 'pointer',
      background: tab === t ? '#3b82f6' : '#e5e7eb',
      color: tab === t ? '#fff' : '#374151'
    }}>{label}</button>
  )

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: 24 }}>
      <button onClick={() => nav('/')} style={{
        background: 'none', border: 'none', cursor: 'pointer', color: '#3b82f6', marginBottom: 12
      }}>← Back</button>

      <h1 style={{ marginBottom: 4 }}>{problem.title}</h1>
      <p style={{ color: '#6b7280', marginBottom: 12 }}>
        {problem.difficulty} · {problem.type} · {problem.time_limit_seconds}s limit
      </p>
      <p style={{ lineHeight: 1.6, marginBottom: 24 }}>{problem.description}</p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <TabBtn t="paste" label="Paste Code" />
        <TabBtn t="upload" label="Upload File" />
      </div>

      {tab === 'paste' ? (
        <textarea
          value={code} onChange={e => setCode(e.target.value)}
          rows={14} placeholder="Paste your solution here…"
          style={{
            width: '100%', fontFamily: 'monospace', fontSize: 13,
            padding: 12, border: '1px solid #d1d5db', borderRadius: 6
          }}
        />
      ) : (
        <div>
          <div
            onClick={() => fileRef.current.click()}
            style={{
              border: '2px dashed #d1d5db', borderRadius: 8, padding: 40,
              textAlign: 'center', cursor: 'pointer', color: '#6b7280'
            }}
          >
            {file ? `📄 ${file.name}` : 'Click to select a file (max 10MB)'}
          </div>
          <input ref={fileRef} type="file" onChange={handleFileChange} style={{ display: 'none' }} />
          {fileError && <p style={{ color: '#dc2626', marginTop: 6, fontSize: 13 }}>{fileError}</p>}
        </div>
      )}

      <button
        onClick={handleSubmit} disabled={!canSubmit}
        style={{
          marginTop: 14, padding: '10px 28px', background: canSubmit ? '#3b82f6' : '#9ca3af',
          color: '#fff', border: 'none', borderRadius: 6, cursor: canSubmit ? 'pointer' : 'default',
          fontSize: 15, fontWeight: 600
        }}
      >
        {loading ? 'Grading…' : 'Submit'}
      </button>
      {loading && <p style={{ color: '#6b7280', marginTop: 6, fontSize: 13 }}>Running in sandbox…</p>}

      <ResultPanel result={result} />
    </div>
  )
}
