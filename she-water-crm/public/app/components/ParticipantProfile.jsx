import React, { useState, useEffect } from 'react'
import { Card, CardHeader, Pill, Loading, Empty, formatDate } from './UI'

const PROGRAM_SCREENS = {
  BW: 'http://localhost:3000/bw.html',
  TW: 'http://localhost:3000/tw.html',
  WQ: 'http://localhost:3000/wq.html',
  WW: 'http://localhost:3000/ww.html',
}

const PHASE_COLORS = {
  investigation:   { bg: 'rgba(59,130,246,0.15)',  color: '#60a5fa' },
  mitigation:      { bg: 'rgba(239,68,68,0.15)',   color: '#ef4444' },
  maintenance:     { bg: 'rgba(34,197,94,0.15)',   color: '#22c55e' },
  closeout:        { bg: 'rgba(100,116,139,0.2)',  color: '#64748b' },
  post_mitigation: { bg: 'rgba(167,139,250,0.15)', color: '#a78bfa' },
}

const STEP_OWNER = {
  field_visit_scheduled:  { label: 'Field Staff',   icon: '🔧' },
  awaiting_lab_results:   { label: 'Lab',           icon: '🧪' },
  results_received:       { label: 'Caseworker',    icon: '👤' },
  closeout_scheduled:     { label: 'Caseworker',    icon: '👤' },
  maintenance_monitoring: { label: 'Caseworker',    icon: '👤' },
  vendor_scheduled:       { label: 'Vendor',        icon: '🚚' },
  pending_approval:       { label: 'Region Mgr',    icon: '⭐' },
}

function MetaItem({ label, value, mono, style }) {
  return (
    <div style={style}>
      <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>{label}</div>
      <div style={{ fontSize: 14, fontFamily: mono ? 'IBM Plex Mono, monospace' : 'inherit' }}>{value || '—'}</div>
    </div>
  )
}

function ProgramCard({ enrollment, onClick }) {
  const code  = enrollment.program_code
  const phase = enrollment.wq_phase
  const step  = enrollment.status_step
  const owner = STEP_OWNER[step]
  const pc    = PHASE_COLORS[phase]

  const programColors = {
    BW: 'var(--bw)', TW: 'var(--tw)', WQ: 'var(--wq)', WW: 'var(--ww)'
  }
  const color = programColors[code] || 'var(--muted)'

  return (
    <div
      onClick={onClick}
      style={{
        background: 'var(--bg)', border: '1px solid var(--border)',
        borderRadius: 10, padding: 16, cursor: 'pointer',
        transition: 'border-color 0.15s',
        borderLeft: `3px solid ${color}`,
      }}
      onMouseEnter={e => e.currentTarget.style.borderColor = color}
      onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
        <Pill label={code} type={code} />
        <span style={{ fontSize: 11, fontFamily: 'IBM Plex Mono, monospace', color: 'var(--muted)' }}>
          {enrollment.program_specific_id}
        </span>
      </div>

      {phase && pc && (
        <div style={{ marginBottom: 8 }}>
          <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600, background: pc.bg, color: pc.color }}>
            {phase.replace('_', ' ')}
          </span>
        </div>
      )}

      {step && owner && (
        <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 6 }}>
          {owner.icon} Ball with: <span style={{ color: 'var(--text)' }}>{owner.label}</span>
        </div>
      )}

      <div style={{ fontSize: 11, color: 'var(--muted)', display: 'flex', gap: 12 }}>
        <span>{enrollment.status_name}</span>
        <span>·</span>
        <span>{enrollment.county_name}</span>
        <span>·</span>
        <span>Since {formatDate(enrollment.enrollment_date)}</span>
      </div>

      <div style={{ marginTop: 10, fontSize: 11, color: color }}>
        Open {code} screen →
      </div>
    </div>
  )
}

function BWTab({ pid }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/bw/participants`)
      .then(r => r.json())
      .then(rows => {
        setData(rows.find(p => p.pid === pid) || null)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [pid])

  if (loading) return <Loading />
  if (!data)   return <Empty message="No active BW enrollment" />

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
      <Card>
        <CardHeader title="Bottled Water Enrollment" />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <MetaItem label="BW Program ID"  value={data.program_specific_id} mono />
          <MetaItem label="Status"         value={data.status_name} />
          <MetaItem label="Vendor"         value={data.vendor_name || 'Not assigned'} />
          <MetaItem label="Household Size" value={data.household_size} />
          <MetaItem label="Allotment"      value={data.allotment_gallons ? `${data.allotment_gallons} gal / delivery` : '—'} />
        </div>
      </Card>
      <Card>
        <CardHeader title="Delivery Status" />
        <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <MetaItem label="Last Delivery" value={formatDate(data.last_delivery)} />
          <MetaItem label="Last Status"   value={data.last_status} />
          <MetaItem label="Next Delivery" value={formatDate(data.next_delivery)} />
        </div>
        <div style={{ padding: '0 16px 16px' }}>
          <a href="http://localhost:3000/bw.html" style={{ display: 'block', padding: '8px 14px', background: 'var(--bw)', color: 'white', borderRadius: 7, fontSize: 12, fontWeight: 600, textAlign: 'center', textDecoration: 'none' }}>
            Open BW Screen →
          </a>
        </div>
      </Card>
    </div>
  )
}

function WQTab({ pid }) {
  const [data, setData] = useState(null)
  const [activities, setActivities] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`/api/wq/participants`)
      .then(r => r.json())
      .then(rows => {
        const match = rows.find(p => p.pid === pid)
        setData(match || null)
        if (match?.case_id) {
          fetch(`/api/case/${match.case_id}/activities`)
            .then(r => r.json())
            .then(acts => setActivities(acts.slice(0, 5)))
        }
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [pid])

  if (loading) return <Loading />
  if (!data)   return <Empty message="No active WQ enrollment" />

  const phase = data.wq_phase
  const step  = data.status_step
  const owner = STEP_OWNER[step]
  const pc    = PHASE_COLORS[phase]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
      <div>
        <Card>
          <CardHeader title="Water Quality Enrollment" />
          <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
            <MetaItem label="WQ Program ID" value={data.program_specific_id} mono />
            {phase && pc && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Phase</div>
                <span style={{ display: 'inline-block', padding: '3px 10px', borderRadius: 4, fontSize: 12, fontWeight: 600, background: pc.bg, color: pc.color }}>
                  {phase.replace('_', ' ')}
                </span>
              </div>
            )}
            {owner && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Ball With</div>
                <div style={{ fontSize: 14 }}>{owner.icon} {owner.label}</div>
              </div>
            )}
            <MetaItem label="Contaminant" value={data.contaminant} />
            {data.value != null && (
              <div>
                <div style={{ fontSize: 11, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 3 }}>Result</div>
                <div style={{ fontSize: 14, fontFamily: 'IBM Plex Mono, monospace', color: data.exceeds_mcl_flag ? 'var(--red)' : 'var(--green)' }}>
                  {data.value} {data.unit} {data.exceeds_mcl_flag ? '⚠ Exceeds MCL' : '✓ Passes'}
                </div>
              </div>
            )}
            <MetaItem label="Equipment" value={data.equipment_type || 'None installed'} />
          </div>
          <div style={{ padding: '0 16px 16px' }}>
            <a href="http://localhost:3000/wq.html" style={{ display: 'block', padding: '8px 14px', background: 'var(--wq)', color: '#000', borderRadius: 7, fontSize: 12, fontWeight: 600, textAlign: 'center', textDecoration: 'none' }}>
              Open WQ Screen →
            </a>
          </div>
        </Card>
      </div>
      <Card>
        <CardHeader title="Recent Activity" />
        <div style={{ padding: '0 4px' }}>
          {activities.length ? activities.map(a => (
            <div key={a.activity_id} style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)', fontSize: 13 }}>
              <div style={{ fontWeight: 500, marginBottom: 2 }}>{a.activity_name}</div>
              <div style={{ fontSize: 11, color: 'var(--muted)' }}>
                {formatDate(a.activity_date)} · {a.performed_by_name || '—'}
              </div>
              {a.notes && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>{a.notes}</div>}
            </div>
          )) : <Empty message="No activities logged" />}
        </div>
        {data.case_id && (
          <div style={{ padding: '8px 16px' }}>
            <a href={`http://localhost:3000/activity.html`} style={{ display: 'block', padding: '6px 14px', background: 'var(--surface)', color: 'var(--cyan)', border: '1px solid var(--border)', borderRadius: 7, fontSize: 12, fontWeight: 600, textAlign: 'center', textDecoration: 'none' }}>
              ⚡ Open Activity Log →
            </a>
          </div>
        )}
      </Card>
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
      .then(d => { setData(d); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [pid])

  if (loading) return <Loading />
  if (error)   return <div style={{ color: 'var(--red)', padding: 24 }}>Error: {error}</div>
  if (!data)   return <Empty />

  const p = data.person
  const activeEnrollments = data.enrollments?.filter(e => !e.exit_date) || []
  const programCodes = [...new Set(activeEnrollments.map(e => e.program_code))]

  // Build tabs dynamically based on active programs
  const baseTabs = ['overview', 'programs', 'cases', 'history']
  const programTabs = programCodes.map(code => ({ id: code.toLowerCase(), label: code, code }))

  return (
    <div>
      {/* HEADER */}
      <Card>
        <div style={{ padding: 24, display: 'grid', gridTemplateColumns: '1fr auto', gap: 20 }}>
          <div>
            <div style={{ fontSize: 26, fontWeight: 600, marginBottom: 4 }}>{p.first_name} {p.last_name}</div>
            <div style={{ fontFamily: 'IBM Plex Mono, monospace', fontSize: 13, color: 'var(--cyan)', marginBottom: 16 }}>{p.pid}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 20 }}>
              <MetaItem label="Phone"     value={p.phone_primary} mono />
              <MetaItem label="Language"  value={p.preferred_language + (p.interpreter_needed ? ' · Interpreter' : '')} />
              <MetaItem label="Household" value={p.household_size} />
              <MetaItem label="Role"      value={p.role_name} />
              <MetaItem label="Caseworker" value={p.caseworker_name} />
              <MetaItem label="Region"    value={p.region_name || 'Unassigned'} />
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
      <div style={{ display: 'flex', gap: 4, marginBottom: 20, borderBottom: '1px solid var(--border)', overflowX: 'auto' }}>
        {baseTabs.map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '10px 16px', fontSize: 13, fontWeight: 500, cursor: 'pointer',
            border: 'none', background: 'none', fontFamily: 'inherit', whiteSpace: 'nowrap',
            color: tab === t ? 'var(--accent)' : 'var(--muted)',
            borderBottom: `2px solid ${tab === t ? 'var(--accent)' : 'transparent'}`,
            marginBottom: -1, textTransform: 'capitalize', transition: 'all 0.15s'
          }}>{t}</button>
        ))}
        {/* Program-specific tabs */}
        {programTabs.map(pt => {
          const colors = { BW: 'var(--bw)', TW: 'var(--tw)', WQ: 'var(--wq)', WW: 'var(--ww)' }
          const c = colors[pt.code] || 'var(--muted)'
          return (
            <button key={pt.id} onClick={() => setTab(pt.id)} style={{
              padding: '10px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer',
              border: 'none', background: 'none', fontFamily: 'inherit', whiteSpace: 'nowrap',
              color: tab === pt.id ? c : 'var(--muted)',
              borderBottom: `2px solid ${tab === pt.id ? c : 'transparent'}`,
              marginBottom: -1, transition: 'all 0.15s'
            }}>{pt.label}</button>
          )
        })}
      </div>

      {/* OVERVIEW */}
      {tab === 'overview' && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          <Card>
            <CardHeader title="Current Location" />
            <div style={{ padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
              <MetaItem label="APN"      value={p.apn_number} mono />
              <MetaItem label="DMPID"    value={p.dmpid || '⚠ Not yet assigned'} mono />
              <MetaItem label="County"   value={p.county_name} />
              <MetaItem label="GSA Zone" value={p.gsa_zone} />
              <MetaItem label="Structure" value={p.structure_type?.replace('_',' ') + (p.unit_number ? ` · ${p.unit_number}` : '')} />
              {p.floodplain_flag && (
                <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 6, padding: '8px 10px', fontSize: 12, color: 'var(--red)' }}>⚠ Floodplain parcel</div>
              )}
              {p.mailing_address && <MetaItem label="Mailing Address" value={p.mailing_address} />}
            </div>
          </Card>
          <Card>
            <CardHeader title="Active Enrollments" />
            <div style={{ padding: '0 16px' }}>
              {activeEnrollments.length ? activeEnrollments.map(e => (
                <div key={e.enrollment_id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 0', borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                  onClick={() => setTab(e.program_code.toLowerCase())}>
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
        <div>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 16 }}>
            Click a program card to view details or open the program screen
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
            {data.enrollments?.map(e => (
              <ProgramCard
                key={e.enrollment_id}
                enrollment={e}
                onClick={() => {
                  const screen = PROGRAM_SCREENS[e.program_code]
                  if (screen) window.open(screen, '_blank')
                }}
              />
            ))}
          </div>
        </div>
      )}

      {/* CASES TAB */}
      {tab === 'cases' && (
        <Card>
          <CardHeader title="Case History" />
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['Case #','Program','Opened','Closed','Status','Phase','Step','Staff','Notes'].map(h => (
                    <th key={h} style={{ padding: '9px 12px', textAlign: 'left', fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--muted)', borderBottom: '1px solid var(--border)', background: 'var(--surface)', whiteSpace: 'nowrap' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.cases?.length ? data.cases.map(c => (
                  <tr key={c.case_id} style={{ cursor: 'pointer' }}
                    onClick={() => window.open(`http://localhost:3000/activity.html`, '_blank')}>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, color: 'var(--cyan)', borderBottom: '1px solid var(--border)' }}>#{c.case_id}</td>
                    <td style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)' }}><Pill label={c.program_code} type={c.program_code} /></td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{formatDate(c.opened_date)}</td>
                    <td style={{ padding: '10px 12px', fontFamily: 'IBM Plex Mono, monospace', fontSize: 12, color: 'var(--muted)', borderBottom: '1px solid var(--border)' }}>{c.closed_date ? formatDate(c.closed_date) : '—'}</td>
                    <td style={{ padding: '10px 12px', borderBottom: '1px solid var(--border)' }}><Pill label={c.case_status} type={c.case_status} /></td>
                    <td style={{ padding: '10px 12px', fontSize: 11, color: 'var(--muted)', borderBottom: '1px solid var(--border)' }}>{c.wq_phase?.replace('_',' ') || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: 11, color: 'var(--muted)', borderBottom: '1px solid var(--border)' }}>{c.status_step || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: 12, borderBottom: '1px solid var(--border)' }}>{c.assigned_staff || '—'}</td>
                    <td style={{ padding: '10px 12px', fontSize: 11, color: 'var(--muted)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', borderBottom: '1px solid var(--border)' }}>{c.notes || '—'}</td>
                  </tr>
                )) : (
                  <tr><td colSpan={9}><Empty message="No cases on record" /></td></tr>
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
            {data.history?.length ? data.history.map((h, i) => (
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

      {/* PROGRAM-SPECIFIC TABS */}
      {tab === 'bw' && <BWTab pid={pid} />}
      {tab === 'wq' && <WQTab pid={pid} />}
      {tab === 'tw' && (
        <Card>
          <CardHeader title="Tank Water" />
          <div style={{ padding: 16, textAlign: 'center' }}>
            <a href="http://localhost:3000/tw.html" style={{ display: 'inline-block', padding: '10px 20px', background: 'var(--tw)', color: 'white', borderRadius: 8, textDecoration: 'none', fontWeight: 600, fontSize: 13 }}>
              Open TW Screen →
            </a>
          </div>
        </Card>
      )}
      {tab === 'ww' && (
        <Card>
          <CardHeader title="Water Well" />
          <div style={{ padding: 16, textAlign: 'center' }}>
            <a href="http://localhost:3000/ww.html" style={{ display: 'inline-block', padding: '10px 20px', background: 'var(--ww)', color: 'white', borderRadius: 8, textDecoration: 'none', fontWeight: 600, fontSize: 13 }}>
              Open WW Screen →
            </a>
          </div>
        </Card>
      )}
    </div>
  )
}
