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
