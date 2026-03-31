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
