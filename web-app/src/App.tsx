import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { CalendarEvent, RunName } from './types'

// Lightweight CSV parser (no quoted-comma support). Matches main.py output headers.
function parseCsvSimple(text: string): Array<Record<string, string>> {
  const lines = text.trim().split(/\r?\n/)
  if (lines.length === 0) return []
  const headers = lines[0].split(',').map((h) => h.trim())
  const rows: Array<Record<string, string>> = []
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(',')
    const row: Record<string, string> = {}
    headers.forEach((h, idx) => {
      row[h] = (cols[idx] ?? '').trim()
    })
    rows.push(row)
  }
  return rows
}

async function getRuns(): Promise<RunName[]> {
  const res = await fetch('/api/runs')
  return (await res.json()) as RunName[]
}

async function getFiles(run: RunName): Promise<string[]> {
  const res = await fetch(`/api/run/${encodeURIComponent(run)}/files`)
  return (await res.json()) as string[]
}

async function getCsv(run: RunName, file: string): Promise<string> {
  const res = await fetch(`/api/run/${encodeURIComponent(run)}/file/${encodeURIComponent(file)}`)
  return await res.text()
}

function rowsToEvents(rows: Array<Record<string, string>>): CalendarEvent[] {
  return rows
    .filter((r) => r['Subject'] && r['Start Date'] && r['Start Time'] && r['End Date'] && r['End Time'])
    .map((r) => {
      const start = new Date(`${r['Start Date']}T${r['Start Time']}:00`)
      const end = new Date(`${r['End Date']}T${r['End Time']}:00`)
      return { title: r['Subject'], start, end }
    })
}

export default function App() {
  const [runs, setRuns] = useState<RunName[]>([])
  const [selectedRun, setSelectedRun] = useState<RunName | null>(null)
  const [files, setFiles] = useState<string[]>([])
  const [index, setIndex] = useState<number>(0)
  const [events, setEvents] = useState<CalendarEvent[]>([])

  const loadRun = useCallback(async (run: RunName) => {
    const fileList = await getFiles(run)
    setFiles(fileList)
    setIndex(0)
    if (fileList.length > 0) {
      const csv = await getCsv(run, fileList[0])
      const rows = parseCsvSimple(csv)
      setEvents(rowsToEvents(rows))
    } else {
      setEvents([])
    }
  }, [])

  const loadIndex = useCallback(
    async (i: number) => {
      if (!selectedRun) return
      if (i < 0 || i >= files.length) return
      setIndex(i)
      const csv = await getCsv(selectedRun, files[i])
      const rows = parseCsvSimple(csv)
      setEvents(rowsToEvents(rows))
    },
    [files, selectedRun]
  )

  useEffect(() => {
    ;(async () => {
      const r = await getRuns()
      setRuns(r)
      if (r.length > 0) {
        setSelectedRun(r[0])
        await loadRun(r[0])
      }
    })()
  }, [loadRun])

  // Compute week start (Monday) based on first event; fallback to current week
  const weekStart = useMemo(() => {
    const base = events.length > 0 ? new Date(events[0].start) : new Date()
    const day = base.getDay() // 0 Sun .. 6 Sat
    const diffToMonday = (day + 6) % 7
    const monday = new Date(base)
    monday.setHours(0, 0, 0, 0)
    monday.setDate(base.getDate() - diffToMonday)
    return monday
  }, [events])

  const weekDays: Date[] = useMemo(() => {
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(weekStart)
      d.setDate(weekStart.getDate() + i)
      return d
    })
  }, [weekStart])

  // Determine visible hour range
  const [minHour, maxHour] = useMemo(() => {
    if (events.length === 0) return [8, 18]
    let minH = 24
    let maxH = 0
    for (const ev of events) {
      minH = Math.min(minH, ev.start.getHours())
      maxH = Math.max(maxH, ev.end.getHours() + (ev.end.getMinutes() > 0 ? 1 : 0))
    }
    minH = Math.min(minH, 8)
    maxH = Math.max(maxH, 17)
    return [minH, maxH]
  }, [events])

  // Keyboard navigation
  const onKey = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'ArrowRight') {
        loadIndex(index + 1)
      } else if (e.key === 'ArrowLeft') {
        loadIndex(index - 1)
      }
    },
    [index, loadIndex]
  )
  const handlerInstalled = useRef(false)
  useEffect(() => {
    if (!handlerInstalled.current) {
      window.addEventListener('keydown', onKey)
      handlerInstalled.current = true
      return () => window.removeEventListener('keydown', onKey)
    }
  }, [onKey])

  // Deterministic color per title
  const colorForTitle = useCallback((title: string) => {
    const hash = Array.from(title).reduce((acc, ch) => acc + ch.charCodeAt(0), 0)
    const hue = hash % 360
    return `hsl(${hue} 70% 45%)`
  }, [])

  // One row per hour block; we render an extra bottom line separately
  const hours = useMemo(() => Array.from({ length: maxHour - minHour }, (_, i) => minHour + i), [minHour, maxHour])
  const gridHeight = hours.length * 60 // 60px per hour

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', fontFamily: 'Inter, system-ui, sans-serif' }}>
      <header style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 16px', borderBottom: '1px solid #e5e7eb' }}>
        <h1 style={{ margin: 0, fontSize: 18 }}>Schedule Viewer</h1>
        <div style={{ flex: 1 }} />
        <label style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, color: '#6b7280' }}>Run</span>
          <select
            value={selectedRun ?? ''}
            onChange={async (e) => {
              const run = e.target.value as RunName
              setSelectedRun(run)
              await loadRun(run)
            }}
            style={{ padding: '6px 8px' }}
          >
            {runs.map((r) => (
              <option key={r} value={r}>{r}</option>
            ))}
          </select>
        </label>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginLeft: 16 }}>
          <button onClick={() => loadIndex(index - 1)} disabled={index <= 0} style={{ padding: '6px 10px' }}>◀</button>
          <div style={{ minWidth: 60, textAlign: 'center' }}>{files.length ? `${index + 1} / ${files.length}` : '0 / 0'}</div>
          <button onClick={() => loadIndex(index + 1)} disabled={index >= files.length - 1} style={{ padding: '6px 10px' }}>▶</button>
        </div>
      </header>

      <div style={{ flex: 1, padding: 12, overflow: 'auto' }}>
        {/* Header row with day names */}
        <div style={{ display: 'grid', gridTemplateColumns: `60px repeat(7, 1fr)`, borderBottom: '1px solid #e5e7eb' }}>
          <div />
          {weekDays.map((d, i) => (
            <div key={i} style={{ padding: '8px 6px', textAlign: 'center', fontWeight: 600 }}>
              {d.toLocaleDateString(undefined, { weekday: 'short' })}
              <div style={{ fontSize: 12, color: '#6b7280' }}>{d.toLocaleDateString()}</div>
            </div>
          ))}
        </div>

        {/* Time grid */}
        <div style={{ display: 'grid', gridTemplateColumns: `60px repeat(7, 1fr)`, position: 'relative' }}>
          {/* Time labels */}
          <div style={{ borderRight: '1px solid #e5e7eb', position: 'relative', height: gridHeight }}>
            {hours.map((h) => (
              <div key={h} style={{ height: 60, position: 'relative' }}>
                <div style={{ position: 'absolute', top: -8, right: 6, fontSize: 11, color: '#6b7280' }}>
                  {new Date(0, 0, 1, h, 0, 0).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit', hour12: true }).toLowerCase()}
                </div>
                <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 1, background: '#e5e7eb' }} />
              </div>
            ))}
            {/* Final bottom boundary line */}
            <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 1, background: '#e5e7eb' }} />
          </div>

          {/* Day columns */}
          {weekDays.map((dayDate, dayIdx) => {
            const dayEvents = events.filter((ev) => ev.start.toDateString() === dayDate.toDateString())
            const totalMinutes = (maxHour - minHour) * 60
            return (
              <div key={dayIdx} style={{ position: 'relative', borderRight: dayIdx < 6 ? '1px solid #f1f5f9' : undefined, height: gridHeight }}>
                {/* Hour lines */}
                {hours.map((h) => (
                  <div key={h} style={{ height: 60, borderBottom: '1px solid #f1f5f9' }} />
                ))}
                {/* Final bottom boundary line to match labels column */}
                <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 1, background: '#f1f5f9' }} />
                {/* Events */}
                {dayEvents.map((ev, idx) => {
                  const startMinutes = (ev.start.getHours() - minHour) * 60 + ev.start.getMinutes()
                  const endMinutes = (ev.end.getHours() - minHour) * 60 + ev.end.getMinutes()
                  const topPct = (startMinutes / totalMinutes) * 100
                  const heightPct = Math.max(2, ((endMinutes - startMinutes) / totalMinutes) * 100)
                  const leftOffset = (idx % 3) * 4 // slight offset for overlaps
                  return (
                    <div
                      key={`${ev.title}-${idx}-${ev.start.toISOString()}`}
                      style={{
                        position: 'absolute',
                        left: 4 + leftOffset,
                        right: 4,
                        top: `${topPct}%`,
                        height: `${heightPct}%`,
                        background: colorForTitle(ev.title),
                        color: 'white',
                        borderRadius: 6,
                        padding: '4px 6px',
                        fontSize: 12,
                        boxShadow: '0 1px 2px rgba(0,0,0,0.15)',
                        overflow: 'hidden',
                      }}
                      title={`${ev.title} — ${ev.start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} - ${ev.end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}
                    >
                      <div style={{ fontWeight: 600, lineHeight: 1.2 }}>{ev.title}</div>
                      <div style={{ opacity: 0.9 }}>{`${ev.start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} — ${ev.end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`}</div>
                    </div>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}


