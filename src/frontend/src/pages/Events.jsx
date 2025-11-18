import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Card, CardContent } from '@mui/material';
import { api } from '../services/api';

export default function Events() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const resp = await api.get('/api/core/events/');
        setEvents(resp.data);
      } catch (err) {
        console.error('Failed to load events', err);
        setError('Failed to load events');
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  if (loading) return <Box p={3}>Loading events...</Box>;
  if (error) return <Box p={3} color="error.main">{error}</Box>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Public events</Typography>
      <Grid container spacing={3}>
        {events.map((ev) => (
          <Grid item xs={12} md={6} key={ev.id}>
            <Card>
              <CardContent>
                <Typography variant="h6">{ev.title}</Typography>
                <Typography color="textSecondary">{new Date(ev.start_time).toLocaleString()} — {ev.location}</Typography>
                <Typography mt={1}>{ev.description}</Typography>
                <Box mt={2}>
                  {ev.generation_status === 'ready' ? (
                    <Box>
                      <Typography variant="subtitle1">Generated content</Typography>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 1 }}>{ev.generated_content?.social_post}</Typography>
                      <Typography variant="caption" display="block">Tone: {ev.generation_meta?.tone} • Brand score: {ev.generation_meta?.brand_score}</Typography>
                    </Box>
                  ) : (
                    <Box>
                      <button
                        onClick={async () => {
                          try {
                            setGenerating(ev.id);
                            const res = await api.post(`/api/core/events/${ev.id}/generate_content/`, { prompt: `Generate multi-channel content for ${ev.title}` });
                            // Update local state
                            setEvents((prev) => prev.map(e => e.id === ev.id ? { ...e, generated_content: res.data.generated_content, generation_meta: res.data.generation_meta, generation_status: 'ready', last_generated_at: new Date().toISOString() } : e));
                          } catch (err) {
                            console.error('Generation failed', err);
                          } finally {
                            setGenerating(null);
                          }
                        }}
                        disabled={generating === ev.id}
                      >{generating === ev.id ? 'Generating…' : 'Generate content'}</button>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
