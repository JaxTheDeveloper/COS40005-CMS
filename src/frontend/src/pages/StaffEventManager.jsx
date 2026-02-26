import React, { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Tab,
  Tabs,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material';
import { CloudUpload as CloudUploadIcon } from '@mui/icons-material';
import { api, authService } from '../services/api';
import EventRefinementChatbot from '../components/EventRefinementChatbot';

function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function StaffEventManager() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({
    generated_content: {},
    generation_status: 'idle',
  });
  const [currentUser, setCurrentUser] = useState(null);
  const [noAccess, setNoAccess] = useState(false);
  const [chatbotOpen, setChatbotOpen] = useState(false);
  const [chatbotEventId, setChatbotEventId] = useState(null);

  useEffect(() => {
    checkAccess();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const checkAccess = async () => {
    try {
      const user = await authService.getCurrentUser();
      setCurrentUser(user);

      const isAuthorized =
        user?.is_staff ||
        ['staff', 'unit_convenor', 'admin'].includes(user?.user_type);

      if (!isAuthorized) {
        setNoAccess(true);
      } else {
        loadEvents();
      }
    } catch (err) {
      console.error(err);
      setNoAccess(true);
    }
  };

  const loadEvents = async () => {
    try {
      setLoading(true);
      const response = await api.get('/core/events/');
      setEvents(response.data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('Failed to load events');
    } finally {
      setLoading(false);
    }
  };

  const handleCSVUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

  const formData = new FormData();
  // Use 'data' key to match the backend expectation and external webhook examples
  formData.append('data', file);

    try {
      setLoading(true);
      const response = await api.post('/core/events/import-csv/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setSuccessMessage(
        `CSV imported successfully: ${response.data.message}`
      );
      setError(null);
      await loadEvents();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.error || 'CSV upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleEditEvent = (event) => {
    setSelectedEvent(event);
    setEditFormData({
      generated_content: event.generated_content || {},
      generation_status: event.generation_status || 'idle',
    });
    setEditDialogOpen(true);
  };

  const handleSaveEvent = async () => {
    try {
      setLoading(true);
      await api.put(
        `/core/events/${selectedEvent.id}/refine_content/`,
        editFormData
      );
      setSuccessMessage('Event content updated successfully');
      setEditDialogOpen(false);
      await loadEvents();
    } catch (err) {
      console.error(err);
      setError('Failed to save event');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateContent = async (eventId) => {
    try {
      setLoading(true);
      await api.post(
        `/core/events/${eventId}/generate_content/`,
        {
          prompt: 'Generate event content',
        }
      );
      setSuccessMessage('Content generation triggered');
      await loadEvents();
    } catch (err) {
      console.error(err);
      setError('Failed to generate content');
    } finally {
      setLoading(false);
    }
  };

  if (noAccess) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Access Denied: You must be HQ Staff or Unit Convenor to manage
          events.
        </Alert>
      </Box>
    );
  }

  const getRoleLabel = () => {
    if (currentUser?.user_type === 'staff') return 'HQ Staff';
    if (currentUser?.user_type === 'unit_convenor') return 'Unit Convenor';
    if (currentUser?.user_type === 'admin') return 'Administrator';
    return 'Staff';
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          mb: 2,
        }}
      >
        <Typography variant="h5">Staff Event Manager</Typography>
        <Chip label={getRoleLabel()} color="primary" variant="outlined" />
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {successMessage && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {successMessage}
        </Alert>
      )}

      <Tabs
        value={tabValue}
        onChange={(e, newValue) => setTabValue(newValue)}
        sx={{ mb: 2 }}
      >
        <Tab label="CSV Import" />
        <Tab label="Manage Events" />
        <Tab label="Notifications" />
      </Tabs>

      <TabPanel value={tabValue} index={0}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Upload Event CSV
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Upload a CSV file with columns: title, description, start, end,
              location, visibility, related_unit_id. The file will be forwarded
              to the n8n workflow for processing.
            </Typography>
            <Box sx={{ mb: 2 }}>
              <input
                type="file"
                accept=".csv"
                onChange={handleCSVUpload}
                style={{ display: 'none' }}
                id="csv-upload"
              />
              <label htmlFor="csv-upload">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                  disabled={loading}
                >
                  {loading ? 'Uploading...' : 'Upload CSV'}
                </Button>
              </label>
            </Box>
            <Typography variant="caption" color="textSecondary">
              Webhook URL:
              https://conditionally-brimful-exie.ngrok-free.dev/webhook-test/import-schedule
            </Typography>
          </CardContent>
        </Card>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        {loading ? (
          <CircularProgress />
        ) : (
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                  <TableCell>Title</TableCell>
                  <TableCell>Start</TableCell>
                  <TableCell>Visibility</TableCell>
                  <TableCell>Generation Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {events.map((event) => (
                  <TableRow key={event.id}>
                    <TableCell>{event.title}</TableCell>
                    <TableCell>
                      {new Date(event.start).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={event.visibility}
                        size="small"
                        color={
                          event.visibility === 'public'
                            ? 'default'
                            : 'primary'
                        }
                      />
                    </TableCell>
                    <TableCell>{event.generation_status}</TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleEditEvent(event)}
                        sx={{ mr: 1 }}
                      >
                        Edit
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          setChatbotEventId(event.id);
                          setChatbotOpen(true);
                        }}
                        sx={{ mr: 1 }}
                      >
                        Refine
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleGenerateContent(event.id)}
                      >
                        Generate
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Typography variant="body2" color="textSecondary">
          Notification management coming soon. Use this tab to send
          notifications to students (attendance, fees, disciplinary actions,
          etc.).
        </Typography>
      </TabPanel>

      <Dialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          Refine Event Content: {selectedEvent?.title}
        </DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          <TextField
            fullWidth
            label="Generation Status"
            value={editFormData.generation_status}
            onChange={(e) =>
              setEditFormData({
                ...editFormData,
                generation_status: e.target.value,
              })
            }
            margin="normal"
            select
            SelectProps={{
              native: true,
            }}
          >
            <option value="idle">Idle</option>
            <option value="pending">Pending</option>
            <option value="ready">Ready</option>
            <option value="failed">Failed</option>
          </TextField>
          <TextField
            fullWidth
            label="Generated Content (JSON)"
            value={JSON.stringify(editFormData.generated_content, null, 2)}
            onChange={(e) => {
              try {
                setEditFormData({
                  ...editFormData,
                  generated_content: JSON.parse(e.target.value),
                });
              } catch (e) {
                // Ignore JSON parse errors
              }
            }}
            margin="normal"
            multiline
            rows={6}
          />
          <Box sx={{ mt: 2 }}>
            <Typography variant="subtitle2">Upload image</Typography>
            <input
              type="file"
              accept="image/*"
              style={{ display: 'none' }}
              id="image-upload"
              onChange={async (e) => {
                const img = e.target.files?.[0];
                if (!img) return;
                const fd = new FormData();
                fd.append('file', img);
                try {
                  setLoading(true);
                  const resp = await api.post('/core/media/', fd, {
                    headers: { 'Content-Type': 'multipart/form-data' },
                  });
                  // Attach uploaded media URL to generated_content.images array
                  const url = resp.data.file;
                  const gc = editFormData.generated_content || {};
                  const images = gc.images || [];
                  images.push(url);
                  setEditFormData({
                    ...editFormData,
                    generated_content: { ...gc, images },
                  });
                  setSuccessMessage('Image uploaded');
                } catch (err) {
                  console.error(err);
                  setError('Failed to upload image');
                } finally {
                  setLoading(false);
                }
              }}
            />
            <label htmlFor="image-upload">
              <Button component="span" variant="outlined" size="small" sx={{ mt: 1 }}>
                Upload Image
              </Button>
            </label>
            {editFormData.generated_content?.images?.length ? (
              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                {editFormData.generated_content.images.map((src, i) => (
                  <img key={i} src={src} alt={`img-${i}`} style={{ maxHeight: 80 }} />
                ))}
              </Box>
            ) : null}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveEvent} variant="contained" disabled={loading}>
            {loading ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={chatbotOpen}
        onClose={() => setChatbotOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>Refine Event Content</DialogTitle>
        <DialogContent sx={{ minHeight: 600 }}>
          {chatbotEventId && (
            <EventRefinementChatbot
              eventId={chatbotEventId}
              onClose={() => setChatbotOpen(false)}
              onPublish={() => {
                setChatbotOpen(false);
                loadEvents();
                setSuccessMessage('Event published successfully');
              }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setChatbotOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
