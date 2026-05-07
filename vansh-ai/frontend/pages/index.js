import { useState, useEffect } from 'react'
import api from '../lib/api'
import { useRouter } from 'next/router'

export default function Home() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)
  const [token, setToken] = useState('')

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
      const res = await api.post('http://localhost:8000/api/query', { query }, { headers })
      setAnswer(res.data.answer)
    } catch (err) {
      console.error(err)
      setAnswer('Error connecting to backend.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-4 font-sans">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Vansh AI</h1>
        {token ? (
          <button
            onClick={handleLogout}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Logout
          </button>
        ) : (
          <span>
            <a href="/login" className="mr-2">Login</a>
            <a href="/signup">Sign up</a>
          </span>
        )}
      </div>

      <p className="mt-4 text-gray-600">Ask me anything!</p>

      <form onSubmit={handleSubmit} className="mt-6">
        <textarea
          rows={4}
          className="w-full p-3 border border-gray-300 rounded resize-y focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your question here..."
        />
        <button
          type="submit"
          disabled={loading}
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </form>

      {answer && (
        <div className="mt-8 p-4 bg-gray-50 rounded border">
          <strong className="block mb-2">Answer:</strong>
          <p className="whitespace-pre-wrap">{answer}</p>
        </div>
      )}
    </div>
  )
}
