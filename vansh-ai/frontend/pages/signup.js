import { useState } from 'react'
import axios from 'axios'
import { useRouter } from 'next/router'

export default function SignUp() {
  const router = useRouter()
  const [form, setForm] = useState({ username: '', email: '', password: '', full_name: '' })
  const [error, setError] = useState('')

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await axios.post('http://localhost:8000/api/auth/signup', form)
      // Store JWT returned by signup (the same payload as login)
      if (res.data && res.data.id) {
        // After signup, we need to login to get a token – call login endpoint automatically
        const loginRes = await axios.post('http://localhost:8000/api/auth/login', {
          username: form.username,
          password: form.password,
        })
        localStorage.setItem('authToken', loginRes.data.access_token)
      }
      router.push('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Signup failed')
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: '2rem auto', fontFamily: 'sans-serif' }}>
      <h1>Sign Up</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '1rem' }}>
          <label>Username</label><br />
          <input name="username" type="text" value={form.username} onChange={handleChange} required style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label>Email</label><br />
          <input name="email" type="email" value={form.email} onChange={handleChange} required style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label>Full Name (optional)</label><br />
          <input name="full_name" type="text" value={form.full_name} onChange={handleChange} style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        <div style={{ marginBottom: '1rem' }}>
          <label>Password</label><br />
          <input name="password" type="password" value={form.password} onChange={handleChange} required style={{ width: '100%', padding: '0.5rem' }} />
        </div>
        <button type="submit" style={{ padding: '0.5rem 1rem', background: '#0070f3', color: 'white', border: 'none', borderRadius: 4 }}>
          Sign Up
        </button>
      </form>
      <p>
        Already have an account? <a href="/login">Log in</a>
      </p>
    </div>
  )
}
