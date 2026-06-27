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
  const [language, setLanguage] = useState('python')
  const fileRef = useRef()

  useEffect(() => {
    fetch(`/api/problems/${id}`)
      .then(r => r.json())
      .then(data => {
        if (data.detail) { nav('/'); return; }
        setProblem(data)
        // Interactive/webapp need real files (index.html); paste only fits algorithm
        setTab(data.type === 'algorithm' ? 'paste' : 'upload')
      })
      .catch(() => nav('/'))
  }, [id])

  function handleFileChange(e) {
    const f = e.target.files[0]
    if (!f) return
    if (f.size > 10 * 1024 * 1024) {
      setFileError('File exceeds the 10MB limit. Trim it down and try again.')
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
    if (problem.type === 'algorithm') form.append('language', language)

    try {
      const res = await fetch(`/api/submit/${id}`, { method: 'POST', body: form })
      const data = await res.json()
      setResult(res.ok ? data : { score: 0, passed: 0, total: 0, results: [], error: data.detail ?? 'Server error' })
    } finally {
      setLoading(false)
    }
  }

  if (!problem) return <main className="page page--narrow"><p className="lead comment">// loading<span className="dots" /></p></main>

  const canSubmit = !loading && (tab === 'paste' ? code.trim() : !!file)
  const Tab = ({ t, label }) => (
    <button className={tab === t ? 'tab tab--on' : 'tab'} onClick={() => setTab(t)}>{label}</button>
  )

  return (
    <main className="page page--narrow">
      <button className="back" onClick={() => nav('/')}>← all problems</button>

      <p className="eyebrow">{problem.id}</p>
      <h1 className="title">{problem.title}</h1>
      <div className="meta">
        <span className="tag">{problem.difficulty}</span>
        <span className="tag">{problem.type}</span>
        <span className="tag">{problem.time_limit_seconds}s limit</span>
      </div>
      <p className="prose">{problem.description}</p>

      {problem.examples && problem.examples.length > 0 && (
        <div className="examples">
          {problem.examples.map((ex, i) => (
            <div className="example" key={i}>
              <div className="example__head">example {i + 1}</div>
              <div className="io">
                <span className="io__k">input</span>
                <pre className="io__v">{ex.input}</pre>
                <span className="io__k">output</span>
                <pre className="io__v">{ex.output}</pre>
              </div>
              {ex.explanation && (
                <div className="example__why"><b>why: </b>{ex.explanation}</div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="pane">
        <div className="pane__bar">
          {problem.type === 'algorithm' && <Tab t="paste" label="Paste code" />}
          <Tab t="upload" label="Upload file" />
          {problem.type === 'algorithm' && (
            <select
              className="select pane__spacer"
              value={language}
              onChange={e => setLanguage(e.target.value)}
            >
              <option value="python">Python 3.11</option>
              <option value="c">C (gcc)</option>
              <option value="cpp">C++ (g++ 17)</option>
            </select>
          )}
        </div>

        {tab === 'paste' ? (
          <textarea
            className="editor"
            value={code}
            onChange={e => setCode(e.target.value)}
            spellCheck={false}
            placeholder="# paste your solution here"
          />
        ) : (
          <>
            <div
              className={file ? 'dropzone dropzone--filled' : 'dropzone'}
              onClick={() => fileRef.current.click()}
            >
              {file ? `📄 ${file.name}` : (problem.type === 'algorithm'
                ? 'Click to choose your solution file · max 10MB'
                : 'Click to choose a .zip containing index.html · max 10MB')}
            </div>
            <input ref={fileRef} type="file" onChange={handleFileChange} style={{ display: 'none' }} />
            {fileError && <p className="file-error">{fileError}</p>}
          </>
        )}
      </div>

      <button className="run" onClick={handleSubmit} disabled={!canSubmit}>
        {loading ? <>grading<span className="dots" /></> : 'Run & grade'}
      </button>
      {loading && <p className="run__hint">// running in an isolated container — no network, capped memory</p>}

      <ResultPanel result={result} />
    </main>
  )
}
