import { useState } from 'react'
import axios from 'axios'
import { useRouter } from 'next/router'

export default function Login() {
  const router = useRouter()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await axios.post('http://localhost:8000/api/auth/login', {
        username,
        password,
      })
      // Store JWT in localStorage
      localStorage.setItem('authToken', res.data.access_token)
      router.push('/') // redirect to home
    } catch (err) {
      setError(err.response?.data?.detail || 'Login failed')
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <h1>Login</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1rem' }}>
          <label>Username</label><br />
          <input
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            style={{ width: '100%', padding: '0.5rem' }}
          />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label>Password</label><br />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: '100%', padding: '0.5rem' }}
          />
        </div>
        <button type="submit" style={{ padding: '0.5rem 1rem', background: '#0070f3', color: 'white', border: 'none', borderRadius: 4 }}>
          Login
        </button>
      </form>
      <p>
        Need an account? <a href="/signup">Sign up</a>
      </p>
    </div>
  )
}
