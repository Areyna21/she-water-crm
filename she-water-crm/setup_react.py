"""
SHE Water CRM — React/Vite Setup Script
Run from inside the she-water-crm folder: python setup_react.py
Does everything in one shot:
  - Creates vite.config.js
  - Updates package.json scripts
  - Creates public/app/index.html
  - Creates public/app/main.jsx
  - Creates public/app/App.jsx
  - Creates public/app/components/ folder structure
  - Installs vite and react plugin
"""

import os
import json
import shutil
import subprocess
from datetime import datetime

def backup(filepath):
    os.makedirs('backups', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    dest = os.path.join('backups', f"{os.path.basename(filepath)}.{ts}.bak")
    shutil.copy2(filepath, dest)
    print(f"  ✓ Backup: {dest}")

def write_file(path, content):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    open(path, 'w', encoding='utf-8').write(content)
    print(f"  ✓ Created: {path}")

print()
print("=" * 55)
print("SHE Water CRM — React/Vite Setup")
print("=" * 55)
print()

# ── CHECK WE ARE IN THE RIGHT FOLDER ─────────────────────────
if not os.path.exists('server.js'):
    print("ERROR: server.js not found.")
    print("Run this from inside the she-water-crm folder.")
    exit()

# ── STEP 1: vite.config.js ───────────────────────────────────
print("Step 1: Creating vite.config.js...")
write_file('vite.config.js', """\
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  root: 'public/app',
  build: {
    outDir: '../../dist',
    emptyOutDir: true,
  },
  server: {
    port: 3001,
    proxy: {
      '/api': 'http://localhost:3000'
    }
  }
})
""")

# ── STEP 2: Update package.json scripts ──────────────────────
print("\nStep 2: Updating package.json...")
backup('package.json')
pkg = json.load(open('package.json', encoding='utf-8'))
pkg['scripts']['dev']   = 'nodemon server.js'
pkg['scripts']['react'] = 'vite'
pkg['scripts']['build'] = 'vite build'
json.dump(pkg, open('package.json', 'w', encoding='utf-8'), indent=2)
print("  ✓ Updated scripts: dev, react, build")

# ── STEP 3: public/app/index.html ────────────────────────────
print("\nStep 3: Creating React entry files...")
os.makedirs('public/app', exist_ok=True)

write_file('public/app/index.html', """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>SHE Water CRM</title>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap" rel="stylesheet">
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/main.jsx"></script>
</body>
</html>
""")

# ── STEP 4: main.jsx ─────────────────────────────────────────
write_file('public/app/main.jsx', """\
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './styles.css'

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
""")

# ── STEP 5: styles.css ───────────────────────────────────────
write_file('public/app/styles.css', """\
:root {
  --bg:      #0f1117;
  --surface: #181c27;
  --border:  #252a38;
  --text:    #e2e8f0;
  --muted:   #64748b;
  --accent:  #3b82f6;
  --green:   #22c55e;
  --yellow:  #f59e0b;
  --red:     #ef4444;
  --purple:  #a78bfa;
  --cyan:    #22d3ee;
  --bw:      #3b82f6;
  --tw:      #22c55e;
  --wq:      #f59e0b;
  --ww:      #a78bfa;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: 'IBM Plex Sans', sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
}

.mono {
  font-family: 'IBM Plex Mono', monospace;
}
""")

# ── STEP 6: App.jsx ──────────────────────────────────────────
write_file('public/app/App.jsx', """\
import React, { useState } from 'react'
import ParticipantSearch from './components/ParticipantSearch'
import ParticipantProfile from './components/ParticipantProfile'
import Nav from './components/Nav'

export default function App() {
  const [page, setPage]               = useState('search')
  const [selectedPID, setSelectedPID] = useState(null)

  function openProfile(pid) {
    setSelectedPID(pid)
    setPage('profile')
  }

  function goBack() {
    setPage('search')
    setSelectedPID(null)
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
""")

# ── STEP 7: Component folder structure ───────────────────────
print("\nStep 4: Creating component files...")
os.makedirs('public/app/components', exist_ok=True)
os.makedirs('public/app/hooks', exist_ok=True)

# Nav component
write_file('public/app/components/Nav.jsx', """\
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
            <a href="/" style={{...btn, textDecoration:'none'}}>Dashboard</a>
            <a href="/bw.html" style={{...btn, textDecoration:'none', color:'var(--bw)'}}>BW</a>
            <a href="/tw.html" style={{...btn, textDecoration:'none', color:'var(--tw)'}}>TW</a>
            <a href="/wq.html" style={{...btn, textDecoration:'none', color:'var(--wq)'}}>WQ</a>
            <a href="/ww.html" style={{...btn, textDecoration:'none', color:'var(--ww)'}}>WW</a>
          </>
        )
      }
    </nav>
  )
}
""")

# useFetch hook
write_file('public/app/hooks/useFetch.js', """\
import { useState, useEffect } from 'react'

export function useFetch(url) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    if (!url) return
    setLoading(true)
    fetch(url)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); })
  }, [url])

  return { data, loading, error }
}
""")

# Shared UI primitives
write_file('public/app/components/UI.jsx', """\
import React from 'react'

export function Pill({ label, type }) {
  const colors = {
    BW:      { bg: 'rgba(59,130,246,0.2)',  color: 'var(--bw)' },
    TW:      { bg: 'rgba(34,197,94,0.2)',   color: 'var(--tw)' },
    WQ:      { bg: 'rgba(245,158,11,0.2)',  color: 'var(--wq)' },
    WW:      { bg: 'rgba(167,139,250,0.2)', color: 'var(--ww)' },
    Active:  { bg: 'rgba(34,197,94,0.15)',  color: 'var(--green)' },
    Closed:  { bg: 'rgba(100,116,139,0.2)', color: 'var(--muted)' },
    open:    { bg: 'rgba(34,197,94,0.15)',  color: 'var(--green)' },
    pending_approval: { bg: 'rgba(245,158,11,0.15)', color: 'var(--yellow)' },
    default: { bg: 'rgba(100,116,139,0.2)', color: 'var(--muted)' },
  }
  const style = colors[type] || colors[label] || colors.default
  return (
    <span style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 20,
      fontSize: 11, fontWeight: 500, background: style.bg, color: style.color
    }}>
      {label}
    </span>
  )
}

export function Card({ children, style }) {
  return (
    <div style={{
      background: 'var(--surface)', border: '1px solid var(--border)',
      borderRadius: 10, overflow: 'hidden', marginBottom: 16, ...style
    }}>
      {children}
    </div>
  )
}

export function CardHeader({ title, children }) {
  return (
    <div style={{
      padding: '12px 16px', borderBottom: '1px solid var(--border)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12
    }}>
      <div style={{ fontSize: 13, fontWeight: 600 }}>{title}</div>
      {children}
    </div>
  )
}

export function StatCard({ label, value, color }) {
  return (
    <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: '14px 16px' }}>
      <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 6 }}>{label}</div>
      <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 24, fontWeight: 600, color: color || 'var(--text)' }}>{value ?? '—'}</div>
    </div>
  )
}

export function Loading() {
  return <div style={{ textAlign: 'center', padding: 40, color: 'var(--muted)', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12 }}>Loading...</div>
}

export function Empty({ message = 'No records found' }) {
  return <div style={{ textAlign: 'center', padding: 40, color: 'var(--muted)', fontSize: 13 }}>{message}</div>
}

export function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}
""")

# ParticipantSearch component
write_file('public/app/components/ParticipantSearch.jsx', """\
import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardHeader, Pill, Loading, Empty } from './UI'

export default function ParticipantSearch({ onSelect }) {
  const [query,        setQuery]        = useState('')
  const [results,      setResults]      = useState([])
  const [loading,      setLoading]      = useState(false)
  const [searched,     setSearched]     = useState(false)

  const search = useCallback(async (q) => {
    setLoading(true)
    setSearched(true)
    try {
      const res  = await fetch(`/api/participants?q=${encodeURIComponent(q)}`)
      const data = await res.json()
      setResults(data)
    } catch(e) { setResults([]) }
    setLoading(false)
  }, [])

  useEffect(() => {
    search('')
  }, [search])

  useEffect(() => {
    const t = setTimeout(() => search(query), 300)
    return () => clearTimeout(t)
  }, [query, search])

  const allotment = (hh) => {
    if (!hh) return '—'
    if (hh <= 2) return '20 gal'
    if (hh <= 4) return '40 gal'
    if (hh <= 6) return '50 gal'
    return '60 gal'
  }

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <div style={{ fontSize: 20, fontWeight: 600, marginBottom: 4 }}>Participants</div>
        <div style={{ fontSize: 13, color: 'var(--muted)' }}>Search by name, PID, phone, or APN</div>
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 16 }}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Search by name, PID, phone, or APN..."
          style={{
            flex: 1, background: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: 8, padding: '10px 14px', color: 'var(--text)',
            fontSize: 14, fontFamily: 'inherit', outline: 'none'
          }}
        />
        <button
          onClick={() => window.location.href = '/intake.html'}
          style={{ padding: '10px 18px', background: 'var(--green)', color: 'white', border: 'none', borderRadius: 8, fontSize: 13, fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit' }}
        >
          + New Participant
        </button>
      </div>

      <Card>
        <CardHeader title={loading ? 'Searching...' : `${results.length} result${results.length !== 1 ? 's' : ''}`} />
        {loading ? <Loading /> : !results.length ? <Empty message="No participants found" /> : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['PID','Name','Phone','Language','APN','County','Structure','Household','Allotment','Programs'].map(h => (
                    <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--muted)', borderBottom: '1px solid var(--border)', whiteSpace: 'nowrap', background: 'var(--surface)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.map(p => (
                  <tr
                    key={p.pid}
                    onClick={() => onSelect(p.pid)}
                    style={{ cursor: 'pointer' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(255,255,255,0.02)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 11, color: 'var(--cyan)', borderBottom: '1px solid var(--border)' }}>{p.pid}</td>
                    <td style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)' }}>
                      <div style={{ fontWeight: 500 }}>{p.last_name}, {p.first_name}</div>
                      {p.interpreter_needed && <div style={{ fontSize: 11, color: 'var(--yellow)' }}>⚑ Interpreter</div>}
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{p.phone_primary || '—'}</td>
                    <td style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)' }}>
                      <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 500, background: p.preferred_language === 'Spanish' ? 'rgba(167,139,250,0.15)' : 'rgba(34,211,238,0.1)', color: p.preferred_language === 'Spanish' ? 'var(--purple)' : 'var(--cyan)' }}>
                        {p.preferred_language}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{p.apn_number || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{p.county_name || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: 12, color: 'var(--muted)', borderBottom: '1px solid var(--border)' }}>{p.structure_type?.replace('_', ' ') || '—'}{p.unit_number ? ` · ${p.unit_number}` : ''}</td>
                    <td style={{ padding: '10px 12px', textAlign: 'center', borderBottom: '1px solid var(--border)' }}>{p.household_size || '—'}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{allotment(p.household_size)}</td>
                    <td style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)' }}>
                      {p.programs && p.programs !== '—'
                        ? p.programs.split(', ').map(code => <Pill key={code} label={code.trim()} type={code.trim()} />)
                        : <span style={{ fontSize: 12, color: 'var(--muted)' }}>None</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}
""")

# ParticipantProfile component
write_file('public/app/components/ParticipantProfile.jsx', """\
import React, { useState, useEffect } from 'react'
import { Card, CardHeader, Pill, Loading, Empty, formatDate } from './UI'

function MetaItem({ label, value, mono, style }) {
  return (
    <div style={style}>
      <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>{label}</div>
      <div style={{ fontSize: 14, fontFamily: mono ? 'IBM Plex Mono, monospace' : 'inherit' }}>{value || '—'}</div>
    </div>
  )
}

export default function ParticipantProfile({ pid, onBack }) {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [tab,     setTab]     = useState('overview')

  useEffect(() => {
    if (!pid) return
    setLoading(true)
    fetch(`/api/participant/${pid}`)
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); })
  }, [pid])

  if (loading) return <Loading />
  if (error)   return <div style={{ color: 'var(--red)', padding: 24 }}>Error: {error}</div>
  if (!data)   return <Empty />

  const p = data.person
  const activeEnrollments = data.enrollments.filter(e => !e.exit_date)
  const tabs = ['overview', 'programs', 'cases', 'history', 'activity']

  return (
    <div>
      {/* HEADER */}
      <Card>
        <div style={{ padding: 24, display: 'grid', gridTemplateColumns: '1fr auto', gap: 20 }}>
          <div>
            <div style={{ fontSize: 26, fontWeight: 600, marginBottom: 4 }}>{p.first_name} {p.last_name}</div>
            <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 13, color: 'var(--cyan)', marginBottom: 16 }}>{p.pid}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20 }}>
              <MetaItem label="Phone" value={p.phone_primary} mono />
              {p.phone_secondary && <MetaItem label="Alt Phone" value={p.phone_secondary} mono />}
              <MetaItem label="Language" value={p.preferred_language + (p.interpreter_needed ? ' — Interpreter needed' : '')} />
              <MetaItem label="Household" value={p.household_size} />
              <MetaItem label="Role" value={p.role_name} />
              <MetaItem label="Caseworker" value={p.caseworker_name} />
              <MetaItem label="Region" value={p.region_name || 'Unassigned'} />
            </div>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'flex-start' }}>
            {activeEnrollments.map(e => (
              <Pill key={e.enrollment_id} label={e.program_code} type={e.program_code} />
            ))}
          </div>
        </div>
      </Card>

      {/* TABS */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid var(--border)' }}>
        {tabs.map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            style={{
              padding: '10px 16px', fontSize: 13, fontWeight: 500, cursor: 'pointer',
              border: 'none', background: 'none', fontFamily: 'inherit',
              color: tab === t ? 'var(--accent)' : 'var(--muted)',
              borderBottom: `2px solid ${tab === t ? 'var(--accent)' : 'transparent'}`,
              marginBottom: -1, textTransform: 'capitalize', transition: 'all 0.15s'
            }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {tab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Card>
            <CardHeader title="Current Location" />
            <div style={{ padding: 16 }}>
              <MetaItem label="APN" value={p.apn_number} mono style={{ marginBottom: 12 }} />
              <MetaItem label="DMPID" value={p.dmpid || '⚠ Not yet assigned'} mono style={{ marginBottom: 12 }} />
              <MetaItem label="County" value={p.county_name} style={{ marginBottom: 12 }} />
              <MetaItem label="GSA Zone" value={p.gsa_zone} style={{ marginBottom: 12 }} />
              <MetaItem label="Structure" value={p.structure_type?.replace('_',' ') + (p.unit_number ? ` · ${p.unit_number}` : '')} style={{ marginBottom: 12 }} />
              {p.floodplain_flag && (
                <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 6, padding: '8px 10px', fontSize: 12, color: 'var(--red)' }}>
                  ⚠ Floodplain parcel
                </div>
              )}
              {p.mailing_address && <MetaItem label="Mailing Address" value={p.mailing_address} style={{ marginTop: 12 }} />}
              {p.structure_lat && (
                <MetaItem label="Coordinates" value={`${p.structure_lat}, ${p.structure_long}`} mono style={{ marginTop: 12 }} />
              )}
            </div>
          </Card>

          <Card>
            <CardHeader title="Active Enrollments" />
            <div style={{ padding: '0 16px' }}>
              {activeEnrollments.length ? activeEnrollments.map(e => (
                <div key={e.enrollment_id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                  <Pill label={e.program_code} type={e.program_code} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, color: 'var(--muted)' }}>{e.program_specific_id}</div>
                    <div style={{ fontSize: 11, color: 'var(--muted)' }}>{e.county_name}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <Pill label={e.status_name} type={e.status_name} />
                    <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>{formatDate(e.enrollment_date)}</div>
                  </div>
                </div>
              )) : <Empty message="No active enrollments" />}
            </div>
          </Card>
        </div>
      )}

      {/* PROGRAMS TAB */}
      {tab === 'programs' && (
        <Card>
          <CardHeader title="All Program Enrollments" />
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Program','ID','County','Structure','Status','Enrolled','Exited','Caseworker'].map(h => (
                    <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--muted)', borderBottom: '1px solid var(--border)', background: 'var(--surface)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.enrollments.map(e => (
                  <tr key={e.enrollment_id}>
                    <td style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)' }}><Pill label={e.program_code} type={e.program_code} /></td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, color: 'var(--muted)', borderBottom: '1px solid var(--border)' }}>{e.program_specific_id}</td>
                    <td style={{ padding: '10px 12px', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{e.county_name}</td>
                    <td style={{ padding: '10px 12px', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{e.structure_type?.replace('_',' ')}{e.unit_number ? ` · ${e.unit_number}` : ''}</td>
                    <td style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)' }}><Pill label={e.status_name} type={e.status_name} /></td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{formatDate(e.enrollment_date)}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, color: e.exit_date ? 'var(--muted)' : 'var(--green)', borderBottom: '1px solid var(--border)' }}>{e.exit_date ? formatDate(e.exit_date) : 'Active'}</td>
                    <td style={{ padding: '10px 12px', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{e.caseworker || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* CASES TAB */}
      {tab === 'cases' && (
        <Card>
          <CardHeader title="Case History" />
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Case #','Program','Opened','Closed','Status','Staff','Notes'].map(h => (
                    <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--muted)', borderBottom: '1px solid var(--border)', background: 'var(--surface)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.cases.length ? data.cases.map(c => (
                  <tr key={c.case_id}>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, color: 'var(--muted)', borderBottom: '1px solid var(--border)' }}>#{c.case_id}</td>
                    <td style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)' }}><Pill label={c.program_code} type={c.program_code} /></td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{formatDate(c.opened_date)}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, color: 'var(--muted)', borderBottom: '1px solid var(--border)' }}>{c.closed_date ? formatDate(c.closed_date) : '—'}</td>
                    <td style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)' }}><Pill label={c.case_status} type={c.case_status} /></td>
                    <td style={{ padding: '10px 12px', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{c.assigned_staff || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: 11, color: 'var(--muted)', maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', borderBottom: '1px solid var(--border)' }}>{c.notes || '—'}</td>
                  </tr>
                )) : (
                  <tr><td colSpan={7}><Empty message="No cases on record" /></td></tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* HISTORY TAB */}
      {tab === 'history' && (
        <Card>
          <CardHeader title="Address History" />
          <div style={{ padding: '0 16px' }}>
            {data.history.length ? data.history.map((h, i) => (
              <div key={i} style={{ padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
                <div style={{ fontWeight: 500, marginBottom: 3 }}>
                  {h.structure_type?.replace('_',' ')} {h.unit_number ? `· ${h.unit_number}` : ''} · {h.apn_number}
                  <span style={{ fontSize: 11, color: 'var(--muted)', marginLeft: 8 }}>{h.county_name}</span>
                </div>
                <div style={{ fontSize: 12, color: 'var(--muted)' }}>
                  {h.role_name} · Household: {h.household_size} · {formatDate(h.start_date)} → {h.end_date ? formatDate(h.end_date) : <span style={{ color: 'var(--green)' }}>Current</span>}
                </div>
              </div>
            )) : <Empty message="No address history" />}
          </div>
        </Card>
      )}

      {/* ACTIVITY TAB */}
      {tab === 'activity' && (
        <Card>
          <CardHeader title="Activity Log" />
          <Empty message="Activity log coming in next build" />
        </Card>
      )}
    </div>
  )
}
""")

print("\nStep 5: Installing Vite and React plugin...")
result = subprocess.run(
    ['npm', 'install', '--save-dev', 'vite', '@vitejs/plugin-react'],
    capture_output=True, text=True
)
if result.returncode == 0:
    print("  ✓ Vite and React plugin installed")
else:
    print(f"  ✗ npm install failed: {result.stderr[:200]}")
    print("  Run manually: npm install --save-dev vite @vitejs/plugin-react")

print()
print("=" * 55)
print("Setup complete.")
print()
print("To start the React dev server:")
print("  npm run react")
print()
print("Open: http://localhost:3001")
print()
print("Keep your API server running on port 3000:")
print("  npm start  (in a separate terminal)")
print()
print("Commit when ready:")
print('  git add .')
print('  git commit -m "add React app with participant search and profile"')
print('  git push')
print()