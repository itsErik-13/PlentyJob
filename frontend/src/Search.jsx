import { useState, useEffect } from 'react'
import { db, auth } from './firebase'
import { collection, addDoc, query, where, getDocs, deleteDoc, doc } from 'firebase/firestore'

function Search() {
    const [queryText, setQueryText] = useState('')
    const [location, setLocation] = useState('')
    const [results, setResults] = useState([])
    const [loading, setLoading] = useState(false)
    const [savedJobs, setSavedJobs] = useState([])
    const [activeTab, setActiveTab] = useState('search') // 'search' or 'saved'

    useEffect(() => {
        if (auth.currentUser) {
            fetchSavedJobs()
        }
    }, [auth.currentUser])

    const fetchSavedJobs = async () => {
        if (!auth.currentUser) return
        const q = query(collection(db, 'saved_jobs'), where('userId', '==', auth.currentUser.uid))
        const querySnapshot = await getDocs(q)
        const jobs = querySnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() }))
        setSavedJobs(jobs)
    }

    const [jobId, setJobId] = useState(null)
    const [jobStatus, setJobStatus] = useState(null)
    const [screenshot, setScreenshot] = useState(null)

    useEffect(() => {
        let interval
        if (jobId && jobStatus !== 'completed') {
            interval = setInterval(checkJobStatus, 2000)
        }
        return () => clearInterval(interval)
    }, [jobId, jobStatus])

    const checkJobStatus = async () => {
        if (!jobId) return
        // Use env var for production, or dynamic hostname for local dev
        const BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`
        const API_URL = `${BASE_URL}/jobs/${jobId}`
        try {
            const response = await fetch(API_URL)
            const data = await response.json()
            setJobStatus(data.status)
            if (data.status === 'completed') {
                setResults(data.results)
                setLoading(false)
            } else if (data.status === 'waiting_input') {
                fetchScreenshot()
            }
        } catch (error) {
            console.error("Error checking job status:", error)
        }
    }

    const fetchScreenshot = async () => {
        if (!jobId) return
        const BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`
        const API_URL = `${BASE_URL}/jobs/${jobId}/screenshot`
        try {
            const response = await fetch(API_URL)
            if (response.ok) {
                const blob = await response.blob()
                setScreenshot(URL.createObjectURL(blob))
            }
        } catch (error) {
            console.error("Error fetching screenshot:", error)
        }
    }

    const handleImageClick = async (e) => {
        if (!jobId) return
        const img = e.target
        const rect = img.getBoundingClientRect()

        // Calculate scale factor (displayed size vs actual screenshot size)
        const scaleX = img.naturalWidth / rect.width
        const scaleY = img.naturalHeight / rect.height

        // Calculate click position relative to the image
        const clickX = e.clientX - rect.left
        const clickY = e.clientY - rect.top

        // Apply scale to get actual coordinates on the server browser
        const x = Math.round(clickX * scaleX)
        const y = Math.round(clickY * scaleY)

        console.log(`Click: Displayed(${clickX}, ${clickY}) -> Server(${x}, ${y})`)

        const BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`
        const API_URL = `${BASE_URL}/jobs/${jobId}/interact`
        try {
            await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'click', x, y })
            })
            // Refresh screenshot after a short delay
            setTimeout(fetchScreenshot, 1000)
        } catch (error) {
            console.error("Error sending click:", error)
        }
    }

    const handleSearch = async (e) => {
        e.preventDefault()
        setLoading(true)
        setResults([])
        setJobId(null)
        setJobStatus(null)
        setScreenshot(null)

        try {
            const BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`
            const API_URL = `${BASE_URL}/jobs/start`
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: queryText, location })
            })
            const data = await response.json()
            setJobId(data.job_id)
            setJobStatus('pending')
        } catch (error) {
            console.error("Search failed:", error)
            alert("Search failed. Ensure backend is running.")
            setLoading(false)
        }
    }

    const saveJob = async (job) => {
        if (!auth.currentUser) return
        try {
            await addDoc(collection(db, 'saved_jobs'), {
                ...job,
                userId: auth.currentUser.uid,
                savedAt: new Date()
            })
            alert('Job saved!')
            fetchSavedJobs()
        } catch (error) {
            console.error("Error saving job:", error)
        }
    }

    const deleteJob = async (id) => {
        try {
            await deleteDoc(doc(db, 'saved_jobs', id))
            fetchSavedJobs()
        } catch (error) {
            console.error("Error deleting job:", error)
        }
    }

    const isJobSaved = (link) => {
        return savedJobs.some(job => job.link === link)
    }

    return (
        <div>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '2rem' }}>
                <button
                    onClick={() => setActiveTab('search')}
                    style={{ opacity: activeTab === 'search' ? 1 : 0.5 }}
                >
                    Search
                </button>
                <button
                    onClick={() => setActiveTab('saved')}
                    style={{ opacity: activeTab === 'saved' ? 1 : 0.5 }}
                >
                    Saved Jobs ({savedJobs.length})
                </button>
            </div>

            {activeTab === 'search' && (
                <>
                    <form onSubmit={handleSearch} className="search-container">
                        <input
                            type="text"
                            placeholder="Job Title (Optional)"
                            value={queryText}
                            onChange={(e) => setQueryText(e.target.value)}
                        />
                        <input
                            type="text"
                            placeholder="Location (e.g. Madrid)"
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            required
                        />
                        <button type="submit" disabled={loading}>
                            {loading ? 'Searching...' : 'Search'}
                        </button>
                    </form>

                    {jobStatus === 'waiting_input' && (
                        <div className="card" style={{ border: '2px solid orange' }}>
                            <h3>⚠️ Manual Action Required</h3>
                            <p>Please solve the CAPTCHA below by clicking on the image.</p>
                            {screenshot ? (
                                <div style={{ position: 'relative', display: 'inline-block' }}>
                                    <img
                                        src={screenshot}
                                        alt="Browser View"
                                        onClick={handleImageClick}
                                        style={{ maxWidth: '100%', cursor: 'crosshair', border: '1px solid #ccc' }}
                                    />
                                    <button
                                        onClick={fetchScreenshot}
                                        style={{ position: 'absolute', top: 5, right: 5, padding: '5px', fontSize: '0.8em' }}
                                    >
                                        🔄 Refresh
                                    </button>
                                </div>
                            ) : (
                                <p>Loading view...</p>
                            )}
                        </div>
                    )}

                    <div className="results-grid">
                        {results.map((job, index) => (
                            <div key={index} className="card">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                    <h3><a href={job.link} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary-color)', textDecoration: 'none' }}>{job.title}</a></h3>
                                    <span title={job.source} style={{ fontSize: '1.5rem' }}>
                                        {job.source === 'InfoJobs' && '🔵'}
                                        {job.source === 'Indeed' && 'ℹ️'}
                                        {job.source === 'LinkedIn' && '💼'}
                                    </span>
                                </div>
                                <p><strong>{job.company}</strong></p>
                                <p>📍 {job.location}</p>
                                {job.salary && job.salary !== 'N/A' && (
                                    <p style={{ color: '#10b981', fontWeight: 'bold' }}>💰 {job.salary}</p>
                                )}
                                <p style={{ fontSize: '0.8em', color: 'gray' }}>Source: {job.source}</p>
                                <button
                                    onClick={() => saveJob(job)}
                                    disabled={isJobSaved(job.link)}
                                    style={{ marginTop: '1rem', fontSize: '0.9em', padding: '0.4em 0.8em' }}
                                >
                                    {isJobSaved(job.link) ? 'Saved' : 'Save Job'}
                                </button>
                            </div>
                        ))}
                        {results.length === 0 && !loading && jobStatus !== 'waiting_input' && <p>No results found (or start a search).</p>}
                    </div>
                </>
            )}

            {activeTab === 'saved' && (
                <div className="results-grid">
                    {savedJobs.map((job) => (
                        <div key={job.id} className="card">
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                <h3><a href={job.link} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--primary-color)', textDecoration: 'none' }}>{job.title}</a></h3>
                                <span title={job.source} style={{ fontSize: '1.5rem' }}>
                                    {job.source === 'InfoJobs' && '🔵'}
                                    {job.source === 'Indeed' && 'ℹ️'}
                                    {job.source === 'LinkedIn' && '💼'}
                                </span>
                            </div>
                            <p><strong>{job.company}</strong></p>
                            <p>📍 {job.location}</p>
                            {job.salary && job.salary !== 'N/A' && (
                                <p style={{ color: '#10b981', fontWeight: 'bold' }}>💰 {job.salary}</p>
                            )}
                            <p style={{ fontSize: '0.8em', color: 'gray' }}>Source: {job.source}</p>
                            <button
                                onClick={() => deleteJob(job.id)}
                                style={{ marginTop: '1rem', fontSize: '0.9em', padding: '0.4em 0.8em', backgroundColor: '#ef4444' }}
                            >
                                Remove
                            </button>
                        </div>
                    ))}
                    {savedJobs.length === 0 && <p>No saved jobs yet.</p>}
                </div>
            )}
        </div>
    )
}

export default Search
