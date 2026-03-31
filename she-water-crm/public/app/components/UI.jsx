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
