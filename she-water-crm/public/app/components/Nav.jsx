import React from 'react'

export default function Nav({ page, onNavigate, onBack }) {
  const brand = { fontFamily: 'IBM Plex Mono, monospace', fontSize: 13, fontWeight: 600, color: 'var(--cyan)', letterSpacing: '0.05em' }
  const nav   = { background: 'var(--surface)', borderBottom: '1px solid var(--border)', padding: '0 24px', display: 'flex', alignItems: 'center', gap: 24, height: 52, position: 'sticky', top: 0, zIndex: 100 }
  const btn   = { padding: '6px 12px', borderRadius: 6, fontSize: 13, color: 'var(--muted)', cursor: 'pointer', border: 'none', background: 'none', fontFamily: 'inherit', transition: 'all 0.15s' }

  return (
    <nav style={nav}>
      <div style={brand}>SHE · WATER CRM</div>
      {page === 'profile'
        ? <button style={btn} onClick={onBack}>← Participants</button>
        : (
          <>
            <button style={{...btn, color: page==='search' ? 'var(--text)' : 'var(--muted)'}} onClick={() => onNavigate('search')}>Participants</button>
            <a href="http://localhost:3000" style={{...btn, textDecoration:'none'}}>Dashboard</a>
            <a href="http://localhost:3000/bw.html" style={{...btn, textDecoration:'none', color:'var(--bw)'}}>BW</a>
            <a href="http://localhost:3000/tw.html" style={{...btn, textDecoration:'none', color:'var(--tw)'}}>TW</a>
            <a href="http://localhost:3000/wq.html" style={{...btn, textDecoration:'none', color:'var(--wq)'}}>WQ</a>
            <a href="http://localhost:3000/ww.html" style={{...btn, textDecoration:'none', color:'var(--ww)'}}>WW</a>
          </>
        )
      }
    </nav>
  )
}
