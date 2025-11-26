import { useState } from 'react'
import { signInWithEmailAndPassword, createUserWithEmailAndPassword } from 'firebase/auth'
import { auth } from './firebase'

function Login() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [isRegistering, setIsRegistering] = useState(false)
    const [error, setError] = useState('')

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError('')
        try {
            if (isRegistering) {
                await createUserWithEmailAndPassword(auth, email, password)
            } else {
                await signInWithEmailAndPassword(auth, email, password)
            }
        } catch (err) {
            setError(err.message)
        }
    }

    return (
        <div className="card" style={{ maxWidth: '400px', margin: '2rem auto' }}>
            <h2>{isRegistering ? 'Register' : 'Login'}</h2>
            {error && <p style={{ color: 'red' }}>{error}</p>}
            <form onSubmit={handleSubmit}>
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                />
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                />
                <button type="submit" style={{ width: '100%' }}>
                    {isRegistering ? 'Sign Up' : 'Sign In'}
                </button>
            </form>
            <p style={{ marginTop: '1rem' }}>
                {isRegistering ? 'Already have an account?' : "Don't have an account?"}{' '}
                <button
                    onClick={() => setIsRegistering(!isRegistering)}
                    style={{ background: 'none', color: 'var(--primary-color)', border: 'none', padding: 0, textDecoration: 'underline' }}
                >
                    {isRegistering ? 'Login' : 'Register'}
                </button>
            </p>
        </div>
    )
}

export default Login
