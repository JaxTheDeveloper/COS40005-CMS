import React, { useEffect, useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  Button,
  IconButton,
} from '@mui/material';
import {
  Close as CloseIcon,
  CheckCircle as CheckCircleIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
  EventNote as EventNoteIcon,
} from '@mui/icons-material';
import { api } from '../services/api';

const notificationTypeIcons = {
  attendance: <CheckCircleIcon sx={{ color: '#4caf50' }} />,
  fees: <WarningIcon sx={{ color: '#ff9800' }} />,
  event: <EventNoteIcon sx={{ color: '#2196f3' }} />,
  disciplinary: <WarningIcon sx={{ color: '#f44336' }} />,
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
      // Load private events (unit-scoped or staff notifications)
      const eventsResponse = await api.get('/core/events/');
      const filteredEvents = eventsResponse.data.filter(
        (event) => event.visibility !== 'public'
      );
      setEvents(filteredEvents);

      // Load system notifications
      try {
        const notifResponse = await api.get('/core/notifications/');
        setNotifications(notifResponse.data);
      } catch (e) {
        // Notifications endpoint may not exist yet
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
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Notifications & Events
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Filter Chips */}
      <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Chip
          label="All"
          onClick={() => setFilterType('all')}
          variant={filterType === 'all' ? 'filled' : 'outlined'}
          color={filterType === 'all' ? 'primary' : 'default'}
        />
        <Chip
          label={`Unread (${notifications.filter((n) => n.unread).length})`}
          onClick={() => setFilterType('unread')}
          variant={filterType === 'unread' ? 'filled' : 'outlined'}
          color={filterType === 'unread' ? 'primary' : 'default'}
        />
        <Chip
          label={`Events (${events.length})`}
          onClick={() => setFilterType('events')}
          variant={filterType === 'events' ? 'filled' : 'outlined'}
          color={filterType === 'events' ? 'primary' : 'default'}
        />
        <Chip
          label={`Notifications (${notifications.length})`}
          onClick={() => setFilterType('notifications')}
          variant={filterType === 'notifications' ? 'filled' : 'outlined'}
          color={filterType === 'notifications' ? 'primary' : 'default'}
        />
      </Box>

      {/* Items List */}
      {filteredItems.length === 0 ? (
        <Alert severity="info">No notifications or events to display</Alert>
      ) : (
        <Grid container spacing={2}>
          {filteredItems.map((item) => {
            const isNotification = item.type === 'notification';
            const data = item.data;

            if (isNotification) {
              return (
                <Grid item xs={12} key={item.id}>
                  <Card
                    sx={{
                      backgroundColor: data.unread ? '#f5f5f5' : '#fafafa',
                      borderLeft: `4px solid ${
                        data.unread ? '#2196f3' : '#ccc'
                      }`,
                    }}
                  >
                    <CardContent sx={{ position: 'relative', pb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                        <Box sx={{ mr: 1, mt: 0.5 }}>
                          {notificationTypeIcons[data.verb?.split('_')[0]] ||
                            <InfoIcon />}
                        </Box>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="subtitle1" fontWeight="bold">
                            {data.verb}
                          </Typography>
                          <Typography variant="body2" color="textSecondary">
                            {data.description || 'No description'}
                          </Typography>
                        </Box>
                        <IconButton
                          size="small"
                          onClick={() => dismissEvent(data.id)}
                          sx={{ ml: 1 }}
                        >
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      </Box>
                      <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
                        <Typography variant="caption" color="textSecondary">
                          {new Date(data.created_at).toLocaleString()}
                        </Typography>
                        {data.unread && (
                          <Button
                            size="small"
                            onClick={() => markAsRead(data.id)}
                          >
                            Mark as read
                          </Button>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            } else {
              // Event card
              return (
                <Grid item xs={12} key={item.id}>
                  <Card sx={{ borderLeft: `4px solid #2196f3` }}>
                    <CardContent sx={{ position: 'relative', pb: 1 }}>
                      <Box sx={{ display: 'flex', alignItems: 'flex-start' }}>
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="subtitle1" fontWeight="bold">
                            {data.title}
                          </Typography>
                          <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                            {data.description}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            📅 {new Date(data.start).toLocaleString()} |{' '}
                            📍 {data.location || 'Online'}
                          </Typography>
                          <br />
                          <Typography variant="caption" color="textSecondary">
                            Visibility: <Chip label={data.visibility} size="small" sx={{ ml: 1 }} />
                          </Typography>
                        </Box>
                        <IconButton
                          size="small"
                          onClick={() => dismissEvent(data.id)}
                          sx={{ ml: 1 }}
                        >
                          <CloseIcon fontSize="small" />
                        </IconButton>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              );
            }
          })}
        </Grid>
      )}
    </Box>
  );
}
