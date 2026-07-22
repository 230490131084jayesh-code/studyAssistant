import React, { useState } from 'react'
import { api } from '../api'

export default function AskPanel({ selectedIds, hasDocuments }) {
  const [question, setQuestion] = useState('')
  const [thread, setThread] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleAsk = async (e) => {
    e.preventDefault()
    if (!question.trim() || loading) return
    setError(null)
    setLoading(true)
    const q = question
    setQuestion('')
    try {
      const result = await api.ask(q, selectedIds)
      setThread((t) => [...t, { question: q, ...result }])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>Ask your documents</h2>
      <p className="panel-sub">Answers are grounded only in what you've uploaded — no outside knowledge.</p>

      <form className="ask-form" onSubmit={handleAsk}>
        <input
          className="ask-input"
          placeholder={hasDocuments ? 'Ask a question about your notes…' : 'Upload a document first'}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={!hasDocuments}
        />
        <button className="btn-primary" disabled={!hasDocuments || loading}>
          {loading ? 'Thinking…' : 'Ask'}
        </button>
      </form>

      {error && <div className="error-banner">{error}</div>}

      {thread.length === 0 && !loading ? (
        <div className="empty-state">Your questions and answers will appear here.</div>
      ) : (
        <div className="qa-thread">
          {thread.slice().reverse().map((entry, i) => (
            <div className="qa-entry" key={i}>
              <div>
                <div className="qa-question">{entry.question}</div>
                <div className="qa-answer">{entry.answer}</div>
              </div>
              <div className="source-stack">
                {entry.sources?.length > 0 && (
                  <p className="section-label" style={{ margin: 0 }}>Sources</p>
                )}
                {entry.sources?.map((s, j) => (
                  <div className="source-card" key={j}>
                    <span className="source-file">{s.filename}</span>
                    {s.location}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
