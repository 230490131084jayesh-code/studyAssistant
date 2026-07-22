import React, { useState } from 'react'
import { api } from '../api'

export default function SummaryPanel({ selectedIds, hasDocuments }) {
  const [style, setStyle] = useState('concise')
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const canGenerate = hasDocuments && selectedIds.length > 0

  const handleGenerate = async () => {
    setError(null)
    setLoading(true)
    try {
      const result = await api.generateSummary(selectedIds, style)
      setSummary(result.summary)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="panel">
      <h2>Summarize</h2>
      <p className="panel-sub">Select one or more documents in the sidebar to condense them.</p>

      <div className="control-row">
        <select value={style} onChange={(e) => setStyle(e.target.value)}>
          <option value="concise">Concise</option>
          <option value="detailed">Detailed</option>
        </select>
        <button className="btn-primary" onClick={handleGenerate} disabled={!canGenerate || loading}>
          {loading ? 'Summarizing…' : 'Generate summary'}
        </button>
      </div>

      {!hasDocuments && <div className="empty-state">Upload a document to get started.</div>}
      {hasDocuments && selectedIds.length === 0 && (
        <div className="empty-state">Select at least one document in the sidebar to summarize.</div>
      )}
      {error && <div className="error-banner">{error}</div>}

      {summary && <div className="summary-box">{summary}</div>}
    </div>
  )
}
