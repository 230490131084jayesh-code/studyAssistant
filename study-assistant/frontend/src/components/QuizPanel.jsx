import React, { useState } from 'react'
import { api } from '../api'

export default function QuizPanel({ selectedIds, hasDocuments }) {
  const [numQuestions, setNumQuestions] = useState(5)
  const [type, setType] = useState('mixed')
  const [questions, setQuestions] = useState([])
  const [selectedAnswers, setSelectedAnswers] = useState({})
  const [submitted, setSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const canGenerate = hasDocuments && selectedIds.length > 0

  const mcqQuestions = questions.filter((q) => q.type === 'mcq')
  const allMcqAnswered = mcqQuestions.every((_, idx) => {
    const originalIndex = questions.indexOf(mcqQuestions[idx])
    return selectedAnswers[originalIndex] !== undefined
  })
  const score = mcqQuestions.reduce((count, q) => {
    const originalIndex = questions.indexOf(q)
    return selectedAnswers[originalIndex] === q.answer ? count + 1 : count
  }, 0)

  const handleGenerate = async () => {
    setError(null)
    setLoading(true)
    setSelectedAnswers({})
    setSubmitted(false)
    try {
      const result = await api.generateQuiz(selectedIds, numQuestions, type)
      setQuestions(result.questions || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = () => {
    setSubmitted(true)
  }

  return (
    <div className="panel">
      <h2>Generate a quiz</h2>
      <p className="panel-sub">Select one or more documents in the sidebar, then build a quiz from just that material.</p>

      <div className="control-row">
        <select value={numQuestions} onChange={(e) => setNumQuestions(Number(e.target.value))}>
          {[3, 5, 8, 10].map((n) => <option key={n} value={n}>{n} questions</option>)}
        </select>
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="mixed">Mixed</option>
          <option value="mcq">Multiple choice</option>
          <option value="short_answer">Short answer</option>
        </select>
        <button className="btn-primary" onClick={handleGenerate} disabled={!canGenerate || loading}>
          {loading ? 'Generating…' : 'Generate quiz'}
        </button>
      </div>

      {!hasDocuments && <div className="empty-state">Upload a document to get started.</div>}
      {hasDocuments && selectedIds.length === 0 && (
        <div className="empty-state">Select at least one document in the sidebar to scope the quiz.</div>
      )}
      {error && <div className="error-banner">{error}</div>}

      {questions.length > 0 && (
        <div className="quiz-list">
          {questions.map((q, i) => (
            <div className="quiz-card" key={i}>
              <div className="quiz-index">Question {i + 1} · {q.type === 'mcq' ? 'multiple choice' : 'short answer'}</div>
              <div className="quiz-question">{q.question}</div>

              {q.type === 'mcq' && q.options && (
                <div className="quiz-options">
                  {q.options.map((opt, j) => {
                    const isSelected = selectedAnswers[i] === opt
                    const isCorrectOpt = opt === q.answer
                    let cls = 'quiz-option'
                    if (isSelected && !submitted) cls += ' selected'
                    if (submitted && isCorrectOpt) cls += ' correct'
                    if (submitted && isSelected && !isCorrectOpt) cls += ' incorrect'
                    return (
                      <div
                        key={j}
                        className={cls}
                        role="button"
                        tabIndex={0}
                        onClick={() => {
                          if (submitted) return
                          setSelectedAnswers((s) => ({ ...s, [i]: opt }))
                        }}
                      >
                        {opt}
                      </div>
                    )
                  })}
                </div>
              )}

              {submitted && (
                <>
                  {q.type !== 'mcq' && <div className="quiz-answer-line">Answer: {q.answer}</div>}
                  {q.explanation && <div className="quiz-explanation">{q.explanation}</div>}
                </>
              )}
            </div>
          ))}

          {!submitted ? (
            <button
              className="btn-primary submit-quiz-btn"
              onClick={handleSubmit}
              disabled={!allMcqAnswered}
              title={!allMcqAnswered ? 'Answer every multiple-choice question to submit' : undefined}
            >
              Submit quiz
            </button>
          ) : (
            <div className="quiz-score-banner">
              {mcqQuestions.length > 0
                ? `You scored ${score} / ${mcqQuestions.length} on multiple choice`
                : 'Answers revealed below'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
