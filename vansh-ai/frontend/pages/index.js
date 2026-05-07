import { useState, useEffect } from 'react'
import axios from 'axios'
import { useRouter } from 'next/router'

export default function Home() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState('')

  // On mount, read token from localStorage
  useEffect(() => {
    const t = localStorage.getItem('authToken')
    setToken(t || '')
  }, [])

  const handleLogout = () => {
    localStorage.removeItem('authToken')
    setToken('')
    router.reload()
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    try {
      const headers = token ? { Authorization: `Bearer ${token}` } : {}
      const res = await axios.post('http://localhost:8000/api/query', { query }, { headers })
      setAnswer(res.data.answer)
    } catch (err) {
      console.error(err)
      setAnswer('Error connecting to backend.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 600, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>Vansh AI</h1>
        {token ? (
          <button onClick={handleLogout} style={{ padding: '0.5rem 1rem', background: '#d32f2f', color: 'white', border: 'none', borderRadius: 4 }}>
            Logout
          </button>
        ) : (
          <span>
            <a href="/login" style={{ marginRight: 8 }}>Login</a>
            <a href="/signup">Sign up</a>
          </span>
        )}
      </div>
      <p>Ask me anything!</p>
      <form onSubmit={handleSubmit}>
        <textarea
          rows={4}
          style={{ width: '100%', padding: '0.5rem' }}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your question here..."
        />
        <button type="submit" disabled={loading} style={{ marginTop: '1rem', padding: '0.5rem 1rem' }}>
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>
      {answer && (
        <div style={{ marginTop: '2rem', padding: '1rem', background: '#f5f5f5' }}>
          <strong>Answer:</strong>
          <p>{answer}</p>
        </div>
      )}
    </div>
  )
}
