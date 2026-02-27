import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

export default function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const resp = await api.get('/core/events/');
        setEvents(resp.data);
      } catch (err) {
        console.error('Failed to load events', err);
        setError('Failed to load events');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) {
    return (
      <section className="stack">
        <p className="lead">Loading events...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="stack">
        <div className="alert alert-error">{error}</div>
      </section>
    );
  }

  return (
    <section className="stack">
      <div className="breadcrumb">Home / <strong>Events</strong></div>
      <h1 className="page-h1">Public Events</h1>

      {events.length === 0 ? (
        <div className="alert alert-info">No events available</div>
      ) : (
        <div className="card-grid">
          {events.map((ev) => (
            <div className="event-card" key={ev.id}>
              <div className="event-card-title">{ev.title}</div>
              <div className="event-card-detail">
                {new Date(ev.start_time).toLocaleString()} — {ev.location}
              </div>
              <p className="news-text">{ev.description}</p>

              {ev.generation_status === 'ready' ? (
                <div className="event-card-content">
                  <div className="icon-card-title">Generated content</div>
                  <p className="news-text" style={{ whiteSpace: 'pre-wrap', marginTop: '0.5rem' }}>
                    {ev.generated_content?.social_post}
                  </p>
                  <div className="event-card-meta">
                    Tone: {ev.generation_meta?.tone} • Brand score: {ev.generation_meta?.brand_score}
                  </div>
                </div>
              ) : (
                <div className="unit-actions">
                  <button
                    className="btn btn-primary"
                    onClick={async () => {
                      try {
                        setGenerating(ev.id);
                        const res = await api.post(`/api/core/events/${ev.id}/generate_content/`, {
                          prompt: `Generate multi-channel content for ${ev.title}`
                        });
                        setEvents((prev) =>
                          prev.map((e) =>
                            e.id === ev.id
                              ? {
                                  ...e,
                                  generated_content: res.data.generated_content,
                                  generation_meta: res.data.generation_meta,
                                  generation_status: 'ready',
                                  last_generated_at: new Date().toISOString(),
                                }
                              : e
                          )
                        );
                      } catch (err) {
                        console.error('Generation failed', err);
                      } finally {
                        setGenerating(null);
                      }
                    }}
                    disabled={generating === ev.id}
                  >
                    {generating === ev.id ? 'Generating…' : 'Generate content'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
