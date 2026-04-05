import React, { useState, useEffect } from 'react'
import ParticipantSearch from './components/ParticipantSearch'
import ParticipantProfile from './components/ParticipantProfile'
import Nav from './components/Nav'

export default function App() {
  const [page, setPage]               = useState('search')
  const [selectedPID, setSelectedPID] = useState(null)

  // Read PID from URL on load — allows deep linking from other screens
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const pid    = params.get('pid')
    if (pid) {
      setSelectedPID(pid)
      setPage('profile')
    }
  }, [])

  function openProfile(pid) {
    setSelectedPID(pid)
    setPage('profile')
    // Update URL so it's bookmarkable
    window.history.pushState({}, '', `?pid=${pid}`)
  }

  function goBack() {
    setPage('search')
    setSelectedPID(null)
    window.history.pushState({}, '', '/')
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      <Nav page={page} onNavigate={setPage} onBack={goBack} />
      <div style={{ maxWidth: 1400, margin: '0 auto', padding: 24 }}>
        {page === 'search'  && <ParticipantSearch onSelect={openProfile} />}
        {page === 'profile' && <ParticipantProfile pid={selectedPID} onBack={goBack} />}
      </div>
    </div>
  )
}
