import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

export default function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        // Backend filters events to only those targeted at the logged-in user
        const resp = await api.get('/core/events/');
        const data = resp.data;
        setEvents(Array.isArray(data) ? data : (data.results || []));
      } catch (err) {
        console.error('Failed to load events', err);
        setError('Failed to load events');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return <section className="stack"><p className="lead">Loading events...</p></section>;
  }

  if (error) {
    return <section className="stack"><div className="alert alert-error">{error}</div></section>;
  }

  return (
    <section className="stack">
      <div className="breadcrumb">Home / <strong>Events</strong></div>
      <h1 className="page-h1">Events for You</h1>

      {events.length === 0 ? (
        <div className="alert alert-info">No events are currently scheduled for you.</div>
      ) : (
        <div className="card-grid">
          {events.map((ev) => (
            <div className="event-card" key={ev.id}>
              <div className="event-card-title">{ev.title}</div>
              <div className="event-card-detail">
                {new Date(ev.start).toLocaleString('en-AU', {
                  weekday: 'short', day: 'numeric', month: 'short',
                  year: 'numeric', hour: '2-digit', minute: '2-digit',
                })}
                {ev.location ? ` · ${ev.location}` : ''}
              </div>

              {/* Show AI-generated social post if ready, otherwise description */}
              {ev.generation_status === 'ready' && ev.generated_content?.social_post ? (
                <p className="news-text" style={{ whiteSpace: 'pre-wrap', marginTop: '0.5rem' }}>
                  {ev.generated_content.social_post}
                </p>
              ) : (
                ev.description && (
                  <p className="news-text" style={{ marginTop: '0.5rem' }}>{ev.description}</p>
                )
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
