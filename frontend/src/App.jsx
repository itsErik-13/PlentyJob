import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { onAuthStateChanged } from 'firebase/auth'
import { auth } from './firebase'
import Login from './Login'
import Search from './Search'

function App() {
  const [theme, setTheme] = useState('light')
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Theme initialization
    const savedTheme = localStorage.getItem('theme') || 'light'
    setTheme(savedTheme)
    document.documentElement.setAttribute('data-theme', savedTheme)

    // Auth listener
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser)
      setLoading(false)
    })

    return () => unsubscribe()
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    document.documentElement.setAttribute('data-theme', newTheme)
  }

  if (loading) return <div className="card">Loading...</div>

  return (
    <Router>
      <div className="app">
        <nav className="navbar">
          <h1>PlentyJob</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {user && <span>{user.email}</span>}
            <button onClick={toggleTheme} className="theme-toggle" title="Toggle Theme">
              {theme === 'light' ? '🌙' : '☀️'}
            </button>
            {user && <button onClick={() => auth.signOut()}>Logout</button>}
          </div>
        </nav>

        <Routes>
          <Route path="/login" element={!user ? <Login /> : <Navigate to="/" />} />
          <Route path="/" element={user ? <Search /> : <Navigate to="/login" />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
