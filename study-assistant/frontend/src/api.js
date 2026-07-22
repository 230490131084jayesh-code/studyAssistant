// Set VITE_API_URL in a .env file (or Render's dashboard) for the deployed backend,
// e.g. VITE_API_URL=https://study-assistant-backend.onrender.com
// Falls back to localhost for local development.
const API_ROOT = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const BASE = `${API_ROOT}/api`

async function handle(res) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

export const api = {
  listDocuments: () => fetch(`${BASE}/documents`).then(handle),

  uploadDocument: (file) => {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE}/documents/upload`, { method: 'POST', body: form }).then(handle)
  },

  deleteDocument: (docId) =>
    fetch(`${BASE}/documents/${docId}`, { method: 'DELETE' }).then(handle),

  ask: (question, docIds) =>
    fetch(`${BASE}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, doc_ids: docIds?.length ? docIds : null }),
    }).then(handle),

  generateQuiz: (docIds, numQuestions, questionType) =>
    fetch(`${BASE}/quiz`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_ids: docIds, num_questions: numQuestions, question_type: questionType }),
    }).then(handle),

  generateSummary: (docIds, style) =>
    fetch(`${BASE}/summary`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ doc_ids: docIds, style }),
    }).then(handle),
}
