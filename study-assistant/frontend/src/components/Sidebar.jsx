import React, { useRef, useState } from 'react'

export default function Sidebar({ documents, selectedIds, onToggleSelect, onUpload, onDelete, uploading }) {
  const fileInput = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleFiles = (files) => {
    Array.from(files).forEach((file) => onUpload(file))
  }

  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-mark" />
        <h1>Study Assistant</h1>
      </div>
      <p className="brand-sub">grounded in your docs only</p>

      <div
        className={`upload-zone${dragging ? ' dragging' : ''}`}
        onClick={() => fileInput.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          handleFiles(e.dataTransfer.files)
        }}
      >
        {uploading ? (
          <span className="loading-dot"><span></span><span></span><span></span></span>
        ) : (
          <>Drop PDF, PPTX or DOCX here, or click to browse</>
        )}
        <input
          ref={fileInput}
          type="file"
          multiple
          accept=".pdf,.pptx,.docx,.txt,.md"
          onChange={(e) => { handleFiles(e.target.files); e.target.value = '' }}
        />
      </div>

      <p className="section-label">Your documents ({documents.length})</p>

      {documents.length === 0 ? (
        <p className="empty-hint">Nothing uploaded yet. Add a file above — answers, quizzes and summaries will only ever come from what's here.</p>
      ) : (
        <ul className="doc-list">
          {documents.map((doc) => (
            <li
              key={doc.doc_id}
              className={`doc-item${selectedIds.includes(doc.doc_id) ? ' selected' : ''}`}
              onClick={() => onToggleSelect(doc.doc_id)}
            >
              <div style={{ flex: 1, overflow: 'hidden' }}>
                <div className="doc-name">{doc.filename}</div>
                <div className="doc-meta">{doc.chunk_count} chunks</div>
              </div>
              <button
                className="doc-remove"
                title="Remove"
                onClick={(e) => { e.stopPropagation(); onDelete(doc.doc_id) }}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}

      {documents.length > 0 && (
        <p className="empty-hint">
          {selectedIds.length === 0
            ? 'No documents selected — Ask will search all of them. Select specific ones to scope quizzes and summaries.'
            : `${selectedIds.length} selected`}
        </p>
      )}
    </aside>
  )
}
