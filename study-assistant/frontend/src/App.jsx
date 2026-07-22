import React, { useEffect, useState, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import AskPanel from './components/AskPanel'
import QuizPanel from './components/QuizPanel'
import SummaryPanel from './components/SummaryPanel'
import { api } from './api'

const TABS = [
  { id: 'ask', label: 'Ask' },
  { id: 'quiz', label: 'Quiz' },
  { id: 'summary', label: 'Summary' },
]

export default function App() {
  const [documents, setDocuments] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [tab, setTab] = useState('ask')
  const [uploading, setUploading] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const docs = await api.listDocuments()
      setDocuments(docs)
    } catch (e) {
      console.error(e)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const handleUpload = async (file) => {
    setUploading(true)
    try {
      await api.uploadDocument(file)
      await refresh()
    } catch (e) {
      alert(`Upload failed: ${e.message}`)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (docId) => {
    try {
      await api.deleteDocument(docId)
      setSelectedIds((ids) => ids.filter((id) => id !== docId))
      await refresh()
    } catch (e) {
      alert(`Delete failed: ${e.message}`)
    }
  }

  const toggleSelect = (docId) => {
    setSelectedIds((ids) =>
      ids.includes(docId) ? ids.filter((id) => id !== docId) : [...ids, docId]
    )
  }

  return (
    <div className="app-shell">
      <Sidebar
        documents={documents}
        selectedIds={selectedIds}
        onToggleSelect={toggleSelect}
        onUpload={handleUpload}
        onDelete={handleDelete}
        uploading={uploading}
      />
      <main className="main">
        <nav className="tabs">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={`tab-btn${tab === t.id ? ' active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>

        {tab === 'ask' && <AskPanel selectedIds={selectedIds} hasDocuments={documents.length > 0} />}
        {tab === 'quiz' && <QuizPanel selectedIds={selectedIds} hasDocuments={documents.length > 0} />}
        {tab === 'summary' && <SummaryPanel selectedIds={selectedIds} hasDocuments={documents.length > 0} />}
      </main>
    </div>
  )
}
