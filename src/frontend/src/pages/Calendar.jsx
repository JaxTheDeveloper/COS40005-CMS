import React, { useEffect, useState, useCallback } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import timeGridPlugin from '@fullcalendar/timegrid';
import { api } from '../services/api';

const WEEKDAY_MAP = {
  'Mon': 1,
  'Tue': 2,
  'Wed': 3,
  'Thu': 4,
  'Fri': 5,
  'Sat': 6,
  'Sun': 0,
  'Monday': 1,
  'Tuesday': 2,
  'Wednesday': 3,
  'Thursday': 4,
  'Friday': 5,
  'Saturday': 6,
  'Sunday': 0,
};

function findFirstDateOnOrAfter(startDate, weekday) {
  const d = new Date(startDate);
  const target = weekday; // 0-6 (Sun-Sat)
  const diff = (target - d.getDay() + 7) % 7;
  d.setDate(d.getDate() + diff);
  return d;
}

function parseNotesForMeeting(notes) {
  if (!notes) return null;
  // notes format from seeder: "Class 3h/week; Mon 09:00"
  const parts = notes.split(';').map(p => p.trim());
  const dayTime = parts.find(p => /\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b/.test(p));
  if (!dayTime) return null;
  const bits = dayTime.split(' ');
  if (bits.length < 2) return null;
  const day = bits[0];
  const time = bits[1];
  return { day, time };
}

export default function CalendarPage() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastLoadedAt, setLastLoadedAt] = useState(null);

  function extractCategory(notes) {
    if (!notes) return null;
    const m = notes.match(/Category:\s*([^;]+)/i);
    if (m) return m[1].trim();
    return null;
  }

  const loadEvents = useCallback(async () => {
    setLoading(true);
    try {
  const resp = await api.get('/enrollment/enrollments/dashboard/');
      const enrollments = resp.data || [];

      const semesterStart = new Date('2025-01-05');
      const weeks = 12;
      const msInWeek = 7 * 24 * 60 * 60 * 1000;

      const evts = [];
      enrollments.forEach(en => {
        const offering = en.offering;
        if (!offering) return;
        const unit = offering.unit || {};
        const notes = offering.notes || '';
        const mt = parseNotesForMeeting(notes);
        if (!mt) return; // skip if no schedule metadata

        const weekdayName = mt.day;
        const time = mt.time; // HH:MM
        const weekday = WEEKDAY_MAP[weekdayName];
        if (weekday === undefined) return;

        const first = findFirstDateOnOrAfter(semesterStart, weekday);
        // set time
        const [hh, mm] = (time || '09:00').split(':').map(x => parseInt(x, 10));
        first.setHours(hh || 9, mm || 0, 0, 0);

        const end = new Date(first.getTime() + weeks * msInWeek);

        const category = extractCategory(notes);
        const color = category === 'core' ? '#2e7d32' : category === 'major' ? '#1565c0' : '#6a1b9a';

        evts.push({
          id: `off-${offering.id}`,
          title: `${unit.code || ''} ${unit.name || ''}`.trim(),
          start: first.toISOString(),
          end: end.toISOString(),
          allDay: false,
          backgroundColor: color,
          borderColor: color,
          extendedProps: { offering, enrollment: en },
        });
      });

      setEvents(evts);
      setLastLoadedAt(new Date());
    } catch (err) {
      console.error('Failed to load enrollments', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  if (loading) return <div>Loading calendar...</div>;

  return (
    <div>
      <h2>Student Calendar (12-week blocks starting 2025-01-05)</h2>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
        <div style={{ color: '#666' }}>Showing 12-week blocks starting 2025-01-05</div>
        <div>
          <button onClick={loadEvents} style={{ marginRight: 8 }}>Refresh</button>
          <span style={{ fontSize: 12, color: '#666' }}>{lastLoadedAt ? `Last updated ${lastLoadedAt.toLocaleTimeString()}` : ''}</span>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ width: 14, height: 14, background: '#2e7d32', display: 'inline-block', borderRadius: 3 }} /> Core</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ width: 14, height: 14, background: '#1565c0', display: 'inline-block', borderRadius: 3 }} /> Major</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><span style={{ width: 14, height: 14, background: '#6a1b9a', display: 'inline-block', borderRadius: 3 }} /> Elective</div>
      </div>

      {events.length === 0 && <div style={{ marginBottom: 12, color: '#666' }}>No scheduled enrolments found — showing empty calendar.</div>}

      <FullCalendar
        plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
        initialView="dayGridMonth"
        initialDate="2025-01-05"
        headerToolbar={{ left: 'prev,next today', center: 'title', right: 'dayGridMonth,timeGridWeek' }}
        events={events}
        height="auto"
      />
    </div>
  );
}
