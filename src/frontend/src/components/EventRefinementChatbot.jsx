import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  Card,
  CardContent,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Chip,
  Grid,
  Typography,
  IconButton,
  Tooltip
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import EditIcon from '@mui/icons-material/Edit';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import { api } from '../services/api';

export default function EventRefinementChatbot({ eventId, onClose, onPublish }) {
  const [tabValue, setTabValue] = useState(0);
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refinementMode, setRefinementMode] = useState('direct_edit'); // 'direct_edit' | 'prompt'
  const [userInput, setUserInput] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedSuggestion, setSelectedSuggestion] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editField, setEditField] = useState('social_post');
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('info');

  useEffect(() => {
    fetchEventDetails();
  }, [eventId]);

  const fetchEventDetails = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/events/${eventId}/get_generation_status/`);
      setEvent(response.data);
    } catch (error) {
      setMessage(`Error loading event: ${error.message}`);
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handlePromptRefinement = async () => {
    if (!userInput.trim()) return;

    try {
      setSubmitting(true);
      const response = await api.post(`/api/events/${eventId}/refine-chatbot/`, {
        refinement_type: 'prompt',
        content: userInput,
        field: editField
      });

      if (response.data.type === 'suggestions') {
        setSuggestions(response.data.suggestions);
        setMessage('Suggestions generated! Select one to apply.');
        setMessageType('success');
      }
    } catch (error) {
      setMessage(`Error: ${error.message}`);
      setMessageType('error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDirectEdit = async () => {
    if (!userInput.trim()) return;

    try {
      setSubmitting(true);
      const response = await api.post(`/api/events/${eventId}/refine-chatbot/`, {
        refinement_type: 'direct_edit',
        content: userInput,
        field: editField
      });

      setEvent({
        ...event,
        generated_content: response.data.generated_content
      });
      setUserInput('');
      setEditMode(false);
      setMessage('Content updated successfully!');
      setMessageType('success');
    } catch (error) {
      setMessage(`Error updating content: ${error.message}`);
      setMessageType('error');
    } finally {
      setSubmitting(false);
    }
  };

  const handleApplySuggestion = async (suggestion) => {
    try {
      setSubmitting(true);
      const response = await api.post(`/api/events/${eventId}/apply-suggestion/`, {
        suggestion,
        field: editField
      });

      setEvent({
        ...event,
        generated_content: response.data.generated_content
      });
      setSuggestions([]);
      setUserInput('');
      setMessage('Suggestion applied successfully!');
      setMessageType('success');
    } catch (error) {
      setMessage(`Error applying suggestion: ${error.message}`);
      setMessageType('error');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const generatedContent = event?.generated_content || {};
  const contentFields = ['social_post', 'email_body', 'article_body', 'vietnamese_social_post', 'vietnamese_email_body', 'vietnamese_article_body'];

  return (
    <Box sx={{ p: 2, maxHeight: '90vh', overflowY: 'auto' }}>
      {message && (
        <Alert severity={messageType} sx={{ mb: 2 }} onClose={() => setMessage('')}>
          {message}
        </Alert>
      )}

      <Typography variant="h6" sx={{ mb: 2 }}>
        Refine Content: {event?.title}
      </Typography>

      {/* Tab navigation for content fields */}
      <Tabs value={tabValue} onChange={(e, val) => { setTabValue(val); setEditField(contentFields[val]); }}>
        {contentFields.map((field) => (
          <Tab key={field} label={field.replace('_', ' ').toUpperCase()} />
        ))}
      </Tabs>

      <Box sx={{ mt: 2 }}>
        {/* Content Preview */}
        <Paper sx={{ p: 2, mb: 3, bgcolor: '#f5f5f5', minHeight: '150px' }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="subtitle2">Current Content</Typography>
            <Tooltip title="Edit directly">
              <IconButton size="small" onClick={() => setEditMode(true)}>
                <EditIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
            {generatedContent[contentFields[tabValue]] || '(No content yet)'}
          </Typography>
        </Paper>

        {/* Refinement Mode Selector */}
        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <Button
            variant={refinementMode === 'direct_edit' ? 'contained' : 'outlined'}
            onClick={() => setRefinementMode('direct_edit')}
            size="small"
          >
            Direct Edit
          </Button>
          <Button
            variant={refinementMode === 'prompt' ? 'contained' : 'outlined'}
            onClick={() => setRefinementMode('prompt')}
            size="small"
          >
            AI Suggestions
          </Button>
        </Box>

        {/* Input Area */}
        {refinementMode === 'direct_edit' && (
          <Paper sx={{ p: 2, mb: 2 }}>
            <TextField
              fullWidth
              multiline
              rows={5}
              placeholder="Type new content here..."
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              disabled={submitting}
              sx={{ mb: 1 }}
            />
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button onClick={() => { setUserInput(''); setEditMode(false); }} disabled={submitting}>
                Cancel
              </Button>
              <Button
                variant="contained"
                endIcon={<SendIcon />}
                onClick={handleDirectEdit}
                disabled={!userInput.trim() || submitting}
              >
                {submitting ? <CircularProgress size={20} sx={{ mr: 1 }} /> : 'Apply Edit'}
              </Button>
            </Box>
          </Paper>
        )}

        {refinementMode === 'prompt' && (
          <Paper sx={{ p: 2, mb: 2 }}>
            <TextField
              fullWidth
              multiline
              rows={3}
              placeholder="e.g., 'Make this more casual' or 'Add emojis' or 'Shorten to 2 sentences'"
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              disabled={submitting}
              sx={{ mb: 1 }}
            />
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
              <Button onClick={() => setUserInput('')} disabled={submitting}>
                Clear
              </Button>
              <Button
                variant="contained"
                endIcon={<SendIcon />}
                onClick={handlePromptRefinement}
                disabled={!userInput.trim() || submitting}
              >
                {submitting ? <CircularProgress size={20} sx={{ mr: 1 }} /> : 'Get Suggestions'}
              </Button>
            </Box>
          </Paper>
        )}

        {/* Suggestions Display */}
        {suggestions.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ mb: 1 }}>
              AI Suggestions - Select one to apply:
            </Typography>
            <Grid container spacing={1}>
              {suggestions.map((suggestion, idx) => (
                <Grid item xs={12} key={idx}>
                  <Card
                    sx={{
                      cursor: 'pointer',
                      border: selectedSuggestion === idx ? '2px solid #1976d2' : '1px solid #e0e0e0',
                      '&:hover': { boxShadow: 2 }
                    }}
                    onClick={() => setSelectedSuggestion(idx)}
                  >
                    <CardContent sx={{ py: 1.5 }}>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Typography variant="body2" sx={{ flex: 1, whiteSpace: 'pre-wrap' }}>
                          {suggestion}
                        </Typography>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleApplySuggestion(suggestion);
                          }}
                          disabled={submitting}
                        >
                          Apply
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Publication Info */}
        <Paper sx={{ p: 2, bgcolor: '#e8f5e9' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <CheckCircleIcon sx={{ color: '#4caf50' }} />
            <Typography variant="body2">
              Status: {event?.generation_status} | Ready to publish: {generatedContent.social_post ? 'Yes ✓' : 'No'}
            </Typography>
          </Box>
        </Paper>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end', mt: 3 }}>
          <Button onClick={onClose}>Close</Button>
          <Button
            variant="contained"
            color="success"
            onClick={() => onPublish(eventId)}
            disabled={!generatedContent.social_post}
          >
            Publish Event
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
