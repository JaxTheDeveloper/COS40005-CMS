import React, { useEffect, useState } from 'react';
import { api } from '../services/api';

const notificationTypeIcons = {
  attendance: '✅',
  fees: '⚠️',
  event: '📅',
  disciplinary: '🚨',
};

export default function StudentNotifications() {
  const [events, setEvents] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [filterType, setFilterType] = useState('all');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const eventsResponse = await api.get('/core/events/');
      const filteredEvents = eventsResponse.data.filter(
        (event) => event.visibility !== 'public'
      );
      setEvents(filteredEvents);

      try {
        const notifResponse = await api.get('/core/notifications/');
        setNotifications(notifResponse.data);
      } catch (e) {
        console.log('Notifications endpoint not available');
      }

      setError(null);
    } catch (err) {
      console.error(err);
      setError('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const markAsRead = async (notificationId) => {
    try {
      await api.patch(`/core/notifications/${notificationId}/`, { unread: false });
      setNotifications(
        notifications.map((n) =>
          n.id === notificationId ? { ...n, unread: false } : n
        )
      );
    } catch (err) {
      console.error(err);
    }
  };

  const dismissEvent = async (eventId) => {
    try {
      await api.patch(`/core/events/${eventId}/`, { dismissed: true });
      setEvents(events.filter((e) => e.id !== eventId));
    } catch (err) {
      console.error(err);
    }
  };

  const allItems = [
    ...notifications.map((n) => ({
      id: `notif-${n.id}`,
      type: 'notification',
      data: n,
    })),
    ...events.map((e) => ({
      id: `event-${e.id}`,
      type: 'event',
      data: e,
    })),
  ].sort((a, b) => {
    const dateA = new Date(a.data.created_at || a.data.start);
    const dateB = new Date(b.data.created_at || b.data.start);
    return dateB - dateA;
  });

  const filteredItems = allItems.filter((item) => {
    if (filterType === 'all') return true;
    if (filterType === 'unread' && item.type === 'notification')
      return item.data.unread;
    if (filterType === 'events' && item.type === 'event') return true;
    if (filterType === 'notifications' && item.type === 'notification')
      return true;
    return false;
  });

  if (loading) {
    return (
      <section className="stack">
        <p className="lead">Loading...</p>
      </section>
    );
  }

  const unreadCount = notifications.filter((n) => n.unread).length;

  return (
    <section className="stack">
      <div className="breadcrumb">Home / <strong>Notifications</strong></div>
      <h1 className="page-h1">Notifications & Events</h1>

      {error && <div className="alert alert-error">{error}</div>}

      {/* Filter Chips */}
      <div className="chip-row">
        <button
          className={`chip ${filterType === 'all' ? 'active' : ''}`}
          onClick={() => setFilterType('all')}
        >
          All
        </button>
        <button
          className={`chip ${filterType === 'unread' ? 'active' : ''}`}
          onClick={() => setFilterType('unread')}
        >
          Unread ({unreadCount})
        </button>
        <button
          className={`chip ${filterType === 'events' ? 'active' : ''}`}
          onClick={() => setFilterType('events')}
        >
          Events ({events.length})
        </button>
        <button
          className={`chip ${filterType === 'notifications' ? 'active' : ''}`}
          onClick={() => setFilterType('notifications')}
        >
          Notifications ({notifications.length})
        </button>
      </div>

      {/* Items List */}
      {filteredItems.length === 0 ? (
        <div className="alert alert-info">No notifications or events to display</div>
      ) : (
        <div className="notif-list">
          {filteredItems.map((item) => {
            const isNotification = item.type === 'notification';
            const data = item.data;

            if (isNotification) {
              return (
                <div
                  key={item.id}
                  className={`notif-card ${data.unread ? 'unread' : 'read'}`}
                >
                  <div className="notif-icon">
                    {notificationTypeIcons[data.verb?.split('_')[0]] || 'ℹ️'}
                  </div>
                  <div className="notif-body">
                    <div className="notif-title">{data.verb}</div>
                    <div className="notif-text">
                      {data.description || 'No description'}
                    </div>
                    <div className="notif-meta">
                      <span className="notif-time">
                        {new Date(data.created_at).toLocaleString()}
                      </span>
                      {data.unread && (
                        <button
                          className="btn"
                          style={{ padding: '0.25rem 0.75rem', fontSize: '0.75rem' }}
                          onClick={() => markAsRead(data.id)}
                        >
                          Mark as read
                        </button>
                      )}
                    </div>
                  </div>
                  <button className="notif-dismiss" onClick={() => dismissEvent(data.id)}>
                    ✕
                  </button>
                </div>
              );
            } else {
              // Event card
              return (
                <div key={item.id} className="notif-card">
                  <div className="notif-icon">📅</div>
                  <div className="notif-body">
                    <div className="notif-title">{data.title}</div>
                    <div className="notif-text">{data.description}</div>
                    <div className="notif-meta">
                      <span className="notif-time">
                        📅 {new Date(data.start).toLocaleString()} | 📍 {data.location || 'Online'}
                      </span>
                      <span className="badge badge-info">{data.visibility}</span>
                    </div>
                  </div>
                  <button className="notif-dismiss" onClick={() => dismissEvent(data.id)}>
                    ✕
                  </button>
                </div>
              );
            }
          })}
        </div>
      )}
    </section>
  );
}
