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
  const [recipients, setRecipients] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [newNotification, setNewNotification] = useState({ recipient: '', verb: '', description: '' });
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

      // load staff/convoc recipients for outgoing messages
      try {
        const usersResp = await api.get('/users/');
        const staffUsers = usersResp.data.filter(
          (u) => ['staff', 'unit_convenor', 'admin'].includes(u.user_type)
        );
        setRecipients(staffUsers);
      } catch (e) {
        console.log('Could not load recipients');
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

      {/* send notification form toggle */}
      <button className="btn" onClick={() => setShowForm(!showForm)}>
        {showForm ? 'Cancel' : 'Send Message'}
      </button>

      {showForm && (
        <div className="card" style={{ margin: '1rem 0', padding: '1rem' }}>
          <h3>Send a message to staff</h3>
          <label>Recipient:</label>
          <select
            value={newNotification.recipient}
            onChange={(e) =>
              setNewNotification({ ...newNotification, recipient: e.target.value })
            }
          >
            <option value="">-- select --</option>
            {recipients.map((r) => (
              <option key={r.id} value={r.id}>
                {r.email} ({r.user_type})
              </option>
            ))}
          </select>
          <label>Subject (verb):</label>
          <input
            type="text"
            value={newNotification.verb}
            onChange={(e) =>
              setNewNotification({ ...newNotification, verb: e.target.value })
            }
          />
          <label>Description:</label>
          <textarea
            value={newNotification.description}
            onChange={(e) =>
              setNewNotification({ ...newNotification, description: e.target.value })
            }
          />
          <button
            className="btn btn-primary"
            onClick={async () => {
              try {
                const resp = await api.post('/core/notifications/', newNotification);
                // don't add to local list since sender isn't the recipient
                setShowForm(false);
                setNewNotification({ recipient: '', verb: '', description: '' });
                // optionally reload notifications so we show any new incoming ones
                loadData();
              } catch (err) {
                console.error(err);
                setError('Failed to send message');
              }
            }}
          >
            Send
          </button>
        </div>
      )}

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
