import React, { useEffect, useState, useCallback } from 'react';
import {
  Box, Button, Card, CardContent, Dialog, DialogActions, DialogContent,
  DialogTitle, TextField, Typography, Alert, CircularProgress, Tab, Tabs,
  Chip, Collapse, IconButton, Divider, Stack, Tooltip, InputAdornment,
  Select, MenuItem, FormControl, InputLabel,
} from '@mui/material';
import { CloudUpload as CloudUploadIcon } from '@mui/icons-material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import PeopleAltIcon from '@mui/icons-material/PeopleAlt';
import AutoFixHighIcon from '@mui/icons-material/AutoFixHigh';
import SearchIcon from '@mui/icons-material/Search';
import { api, authService } from '../services/api';
import EventRefinementChatbot from '../components/EventRefinementChatbot';
import EventTargeting from '../components/EventTargeting';

function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

const STATUS_COLORS = {
  idle: 'default',
  pending: 'warning',
  ready: 'success',
  failed: 'error',
};

const VISIBILITY_COLORS = {
  public: 'success',
  unit: 'primary',
  staff: 'secondary',
};

const CONTENT_KEYS = ['social_post', 'email_newsletter', 'recruitment_ad', 'vietnamese_version'];

// Single expandable event row — loads detail lazily on expand
function EventRow({ event: initialEvent, onRefine, onAudience, onGenerate, onRefresh }) {
  const [open, setOpen] = useState(false);
  const [event, setEvent] = useState(initialEvent);
  const [detail, setDetail] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  // Sync if parent refreshes
  useEffect(() => { setEvent(initialEvent); }, [initialEvent]);

  const handleExpand = async () => {
    const next = !open;
    setOpen(next);
    if (next && !detail) {
      try {
        setLoadingDetail(true);
        const res = await api.get(`/core/events/${event.id}/get_generation_status/`);
        setDetail(res.data);
      } catch (e) {
        setDetail({ error: 'Failed to load details' });
      } finally {
        setLoadingDetail(false);
      }
    }
  };

  const hasContent = detail && Object.keys(detail.generated_content || {}).length > 0;

  return (
    <Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, mb: 1, overflow: 'hidden' }}>
      {/* Row header — always visible */}
      <Box
        sx={{
          display: 'flex', alignItems: 'center', px: 2, py: 1.5,
          bgcolor: open ? 'grey.50' : 'background.paper',
          cursor: 'pointer', '&:hover': { bgcolor: 'grey.50' },
          gap: 1,
        }}
        onClick={handleExpand}
      >
        <IconButton size="small" sx={{ mr: 0.5 }}>
          {open ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
        </IconButton>

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="body2" fontWeight={600} noWrap>{event.title}</Typography>
          <Typography variant="caption" color="text.secondary">
            {new Date(event.start).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })}
            {event.location ? ` · ${event.location}` : ''}
          </Typography>
        </Box>

        <Stack direction="row" spacing={0.5} alignItems="center" onClick={e => e.stopPropagation()}>
          <Chip
            size="small"
            label={event.visibility}
            color={VISIBILITY_COLORS[event.visibility] || 'default'}
            variant="outlined"
          />
          <Chip
            size="small"
            label={event.generation_status}
            color={STATUS_COLORS[event.generation_status] || 'default'}
          />
          <Tooltip title="Refine with AI">
            <IconButton size="small" color="primary" onClick={() => onRefine(event.id)}>
              <AutoFixHighIcon fontSize="small" />
            </IconButton>
          </Tooltip>
          <Tooltip title="Audience settings">
            <IconButton size="small" onClick={() => onAudience(event.id)}>
              <PeopleAltIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
      </Box>

      {/* Expanded detail */}
      <Collapse in={open} unmountOnExit>
        <Divider />
        <Box sx={{ px: 2, py: 2, bgcolor: 'grey.50' }}>
          {loadingDetail && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CircularProgress size={16} />
              <Typography variant="caption" color="text.secondary">Loading…</Typography>
            </Box>
          )}

          {detail?.error && (
            <Alert severity="error" sx={{ mb: 1 }}>{detail.error}</Alert>
          )}

          {detail && !detail.error && (
            <>
              {/* Description / content remarks */}
              {event.description && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ textTransform: 'uppercase' }}>
                    Description / Content Remarks
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 0.5 }}>{event.description}</Typography>
                </Box>
              )}

              {/* CSV meta if present */}
              {detail.generation_meta?.csv_meta && (
                <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {detail.generation_meta.csv_meta.notify_rule && (
                    <Chip size="small" label={`Notify: ${detail.generation_meta.csv_meta.notify_rule}`} variant="outlined" />
                  )}
                  {detail.generation_meta.csv_meta.channels && (
                    <Chip size="small" label={`Channels: ${detail.generation_meta.csv_meta.channels}`} variant="outlined" />
                  )}
                  {detail.generation_meta.csv_meta.target_audience && (
                    <Chip size="small" label={`Audience: ${detail.generation_meta.csv_meta.target_audience}`} variant="outlined" />
                  )}
                </Box>
              )}

              {/* Generated content panels */}
              {hasContent ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
                  {CONTENT_KEYS.filter(k => detail.generated_content[k]).map(key => (
                    <Box key={key} sx={{ bgcolor: 'background.paper', border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 1.5 }}>
                      <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ textTransform: 'uppercase' }}>
                        {key.replace(/_/g, ' ')}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 0.5, whiteSpace: 'pre-wrap' }}>
                        {detail.generated_content[key]}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 1 }}>
                  <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    No AI content yet.
                  </Typography>
                  <Button size="small" variant="outlined" onClick={() => onGenerate(event.id)}>
                    Generate
                  </Button>
                </Box>
              )}

              {/* Confirmed by */}
              {detail.generation_meta?.confirmed_by && (
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Confirmed by {detail.generation_meta.confirmed_by} · {detail.generation_meta.confirmed_at?.slice(0, 10)}
                </Typography>
              )}
            </>
          )}
        </Box>
      </Collapse>
    </Box>
  );
}

export default function StaffEventManager() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [currentUser, setCurrentUser] = useState(null);
  const [noAccess, setNoAccess] = useState(false);

  // Dialogs
  const [chatbotEventId, setChatbotEventId] = useState(null);
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [audienceEventId, setAudienceEventId] = useState(null);
  const [audienceOpen, setAudienceOpen] = useState(false);

  // Filters
  const [search, setSearch] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterVisibility, setFilterVisibility] = useState('all');

  useEffect(() => {
    checkAccess();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const checkAccess = async () => {
    try {
      const user = await authService.getCurrentUser();
      setCurrentUser(user);
      const isAuthorized = user?.is_staff || ['staff', 'unit_convenor', 'admin'].includes(user?.user_type);
      if (!isAuthorized) { setNoAccess(true); } else { loadEvents(); }
    } catch { setNoAccess(true); }
  };

  const loadEvents = async () => {
    try {
      setLoading(true);
      const res = await api.get('/core/events/');
      const data = res.data;
      setEvents(Array.isArray(data) ? data : (data.results || []));
      setError(null);
    } catch { setError('Failed to load events'); }
    finally { setLoading(false); }
  };

  const handleCSVUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('data', file);
    try {
      setLoading(true);
      const res = await api.post('/core/events/import-csv/', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setSuccessMessage(`CSV imported: ${res.data.message}`);
      await loadEvents();
    } catch (err) {
      setError(err.response?.data?.error || 'CSV upload failed');
    } finally { setLoading(false); }
  };

  const handleGenerateContent = async (eventId) => {
    try {
      await api.post(`/core/events/${eventId}/generate_content/`, { prompt: 'Generate event content' });
      setSuccessMessage('Content generation triggered');
      await loadEvents();
    } catch { setError('Failed to generate content'); }
  };

  const getRoleLabel = () => {
    if (currentUser?.user_type === 'staff') return 'HQ Staff';
    if (currentUser?.user_type === 'unit_convenor') return 'Unit Convenor';
    if (currentUser?.user_type === 'admin') return 'Administrator';
    return 'Staff';
  };

  // Apply filters
  const filtered = events.filter(ev => {
    const matchSearch = !search || ev.title.toLowerCase().includes(search.toLowerCase());
    const matchStatus = filterStatus === 'all' || ev.generation_status === filterStatus;
    const matchVis = filterVisibility === 'all' || ev.visibility === filterVisibility;
    return matchSearch && matchStatus && matchVis;
  });

  if (noAccess) {
    return <Box sx={{ p: 3 }}><Alert severity="error">Access Denied: You must be HQ Staff or Unit Convenor.</Alert></Box>;
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h5">Staff Event Manager</Typography>
        <Chip label={getRoleLabel()} color="primary" variant="outlined" />
      </Box>

      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
      {successMessage && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccessMessage(null)}>{successMessage}</Alert>}

      <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)} sx={{ mb: 2 }}>
        <Tab label="Manage Events" />
        <Tab label="CSV Import" />
        <Tab label="Notifications" />
      </Tabs>

      {/* ── Manage Events ── */}
      <TabPanel value={tabValue} index={0}>
        {/* Filter bar */}
        <Stack direction="row" spacing={1} sx={{ mb: 2 }} flexWrap="wrap">
          <TextField
            size="small"
            placeholder="Search events…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon fontSize="small" /></InputAdornment> }}
            sx={{ minWidth: 220 }}
          />
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Status</InputLabel>
            <Select value={filterStatus} label="Status" onChange={e => setFilterStatus(e.target.value)}>
              <MenuItem value="all">All statuses</MenuItem>
              <MenuItem value="idle">Idle</MenuItem>
              <MenuItem value="pending">Pending</MenuItem>
              <MenuItem value="ready">Ready</MenuItem>
              <MenuItem value="failed">Failed</MenuItem>
            </Select>
          </FormControl>
          <FormControl size="small" sx={{ minWidth: 140 }}>
            <InputLabel>Visibility</InputLabel>
            <Select value={filterVisibility} label="Visibility" onChange={e => setFilterVisibility(e.target.value)}>
              <MenuItem value="all">All</MenuItem>
              <MenuItem value="public">Public</MenuItem>
              <MenuItem value="unit">Unit</MenuItem>
              <MenuItem value="staff">Staff only</MenuItem>
            </Select>
          </FormControl>
          <Box sx={{ flex: 1 }} />
          <Button size="small" variant="outlined" onClick={loadEvents} disabled={loading}>
            {loading ? <CircularProgress size={14} sx={{ mr: 0.5 }} /> : null}
            Refresh
          </Button>
        </Stack>

        {loading && events.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : filtered.length === 0 ? (
          <Typography variant="body2" color="text.secondary" sx={{ py: 3, textAlign: 'center' }}>
            No events match your filters.
          </Typography>
        ) : (
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
              {filtered.length} event{filtered.length !== 1 ? 's' : ''} — click a row to expand
            </Typography>
            {filtered.map(ev => (
              <EventRow
                key={ev.id}
                event={ev}
                onRefine={(id) => { setChatbotEventId(id); setChatbotOpen(true); }}
                onAudience={(id) => { setAudienceEventId(id); setAudienceOpen(true); }}
                onGenerate={handleGenerateContent}
                onRefresh={loadEvents}
              />
            ))}
          </Box>
        )}
      </TabPanel>

      {/* ── CSV Import ── */}
      <TabPanel value={tabValue} index={1}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>Upload Event CSV</Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Supports both simple format (title, description, start, end, location, visibility)
              and rich CSV format (Event_Title, Event_Date, Start_Time, Location, Notify_Rule,
              Channels, Target_Audience, Content_Remarks, Assets_URL).
            </Typography>
            <input type="file" accept=".csv" onChange={handleCSVUpload}
              style={{ display: 'none' }} id="csv-upload" />
            <label htmlFor="csv-upload">
              <Button variant="contained" component="span" startIcon={<CloudUploadIcon />} disabled={loading}>
                {loading ? 'Uploading…' : 'Upload CSV'}
              </Button>
            </label>
          </CardContent>
        </Card>
      </TabPanel>

      {/* ── Notifications ── */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="body2" color="textSecondary">
          Notification management coming soon.
        </Typography>
      </TabPanel>

      {/* Chatbot dialog */}
      <Dialog open={chatbotOpen} onClose={() => setChatbotOpen(false)} maxWidth="lg" fullWidth>
        <DialogTitle>Refine Event Content</DialogTitle>
        <DialogContent sx={{ minHeight: 600 }}>
          {chatbotEventId && (
            <EventRefinementChatbot
              eventId={chatbotEventId}
              onClose={() => { setChatbotOpen(false); loadEvents(); }}
              onPublish={() => { setChatbotOpen(false); loadEvents(); setSuccessMessage('Event confirmed and published'); }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChatbotOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>

      {/* Audience dialog */}
      <Dialog open={audienceOpen} onClose={() => setAudienceOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Audience Settings</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {audienceEventId && (
            <EventTargeting
              eventId={audienceEventId}
              onSave={() => { setAudienceOpen(false); loadEvents(); setSuccessMessage('Audience saved'); }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAudienceOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
