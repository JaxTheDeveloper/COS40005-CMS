import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Typography,
  Divider,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { api } from '../services/api';

const CONTENT_KEYS = ['social_post', 'email_newsletter', 'recruitment_ad', 'vietnamese_version'];

function ContentPreview({ content }) {
  if (!content || Object.keys(content).length === 0) {
    return (
      <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
        No content yet — send a refinement prompt to generate.
      </Typography>
    );
  }
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {CONTENT_KEYS.filter(k => content[k]).map(key => (
        <Box key={key}>
          <Typography variant="caption" color="text.secondary" sx={{ textTransform: 'uppercase', fontWeight: 600 }}>
            {key.replace(/_/g, ' ')}
          </Typography>
          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap', mt: 0.5 }}>
            {content[key]}
          </Typography>
        </Box>
      ))}
    </Box>
  );
}

function ChatBubble({ role, text }) {
  const isUser = role === 'user';
  return (
    <Box sx={{ display: 'flex', justifyContent: isUser ? 'flex-end' : 'flex-start', mb: 1 }}>
      <Paper
        elevation={0}
        sx={{
          px: 2, py: 1,
          maxWidth: '80%',
          bgcolor: isUser ? 'primary.main' : 'grey.100',
          color: isUser ? 'white' : 'text.primary',
          borderRadius: isUser ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
        }}
      >
        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{text}</Typography>
      </Paper>
    </Box>
  );
}

export default function EventRefinementChatbot({ eventId, onClose, onPublish }) {
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [currentContent, setCurrentContent] = useState({});
  const [error, setError] = useState('');
  const [confirming, setConfirming] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    fetchEvent();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [eventId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, submitting]);

  const fetchEvent = async () => {
    try {
      setLoading(true);
      const res = await api.get(`/api/core/events/${eventId}/get_generation_status/`);
      setEvent(res.data);
      setCurrentContent(res.data.generated_content || {});
    } catch (err) {
      setError('Failed to load event details.');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    const trimmed = prompt.trim();
    if (!trimmed || submitting) return;

    const userTurn = { role: 'user', content: trimmed };
    const updatedHistory = [...chatHistory, userTurn];
    setChatHistory(updatedHistory);
    setPrompt('');
    setSubmitting(true);
    setError('');

    try {
      const res = await api.post(`/api/core/events/${eventId}/refine_content/`, {
        refinement_prompt: trimmed,
        current_content: currentContent,
        chat_history: chatHistory, // send history before this turn
      });

      const refined = res.data.generated_content || {};
      setCurrentContent(refined);

      // Build a short assistant summary for the chat
      const summary = refined.social_post
        ? `Done! Here's the updated content:\n\n${refined.social_post.substring(0, 120)}${refined.social_post.length > 120 ? '…' : ''}`
        : 'Content updated.';

      setChatHistory(prev => [...prev, { role: 'assistant', content: summary }]);
    } catch (err) {
      const msg = err.response?.data?.detail || err.response?.data?.error || 'Refinement failed.';
      setError(msg);
      // Remove the user turn we optimistically added
      setChatHistory(chatHistory);
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleConfirm = async (visibility = 'public') => {
    try {
      setConfirming(true);
      await api.post(`/api/core/events/${eventId}/confirm-content/`, { visibility });
      onPublish && onPublish(eventId);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to confirm event.');
    } finally {
      setConfirming(false);
    }
  };

  const handleClearContent = async () => {
    try {
      await api.delete(`/api/core/events/${eventId}/clear-content/`);
      setCurrentContent({});
      setChatHistory([]);
      setError('');
    } catch (err) {
      setError('Failed to clear content.');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  const hasContent = Object.keys(currentContent).length > 0;
  const isReady = event?.generation_status === 'ready' || hasContent;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 560 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
        <Box>
          <Typography variant="subtitle1" fontWeight={600}>{event?.title}</Typography>
          <Chip
            size="small"
            label={event?.generation_status || 'idle'}
            color={isReady ? 'success' : 'default'}
            sx={{ mt: 0.5 }}
          />
        </Box>
        {hasContent && (
          <Tooltip title="Clear all generated content">
            <IconButton size="small" onClick={handleClearContent} color="error">
              <DeleteOutlineIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      <Divider sx={{ mb: 1 }} />

      {error && (
        <Alert severity="error" sx={{ mb: 1 }} onClose={() => setError('')}>{error}</Alert>
      )}

      {/* Main layout: chat left, content preview right */}
      <Box sx={{ display: 'flex', gap: 2, flex: 1, overflow: 'hidden' }}>

        {/* Chat column */}
        <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
          {/* Message history */}
          <Box sx={{ flex: 1, overflowY: 'auto', pr: 1, mb: 1 }}>
            {chatHistory.length === 0 && (
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic', mt: 2 }}>
                Type a refinement prompt below. Each message refines the content further.
                When you're happy, click Confirm &amp; Publish.
              </Typography>
            )}
            {chatHistory.map((turn, i) => (
              <ChatBubble key={i} role={turn.role} text={turn.content} />
            ))}
            {submitting && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                <CircularProgress size={16} />
                <Typography variant="caption" color="text.secondary">Groq is refining…</Typography>
              </Box>
            )}
            <div ref={bottomRef} />
          </Box>

          {/* Input */}
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              size="small"
              placeholder="e.g. Make the social post more casual and add emojis"
              value={prompt}
              onChange={e => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={submitting}
            />
            <Button
              variant="contained"
              onClick={handleSend}
              disabled={!prompt.trim() || submitting}
              sx={{ minWidth: 44, px: 1.5, height: 40 }}
            >
              <SendIcon fontSize="small" />
            </Button>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
            Shift+Enter for new line · Enter to send
          </Typography>
        </Box>

        {/* Content preview column */}
        <Box sx={{ width: 340, flexShrink: 0, display: 'flex', flexDirection: 'column' }}>
          <Typography variant="caption" color="text.secondary" fontWeight={600} sx={{ mb: 1, textTransform: 'uppercase' }}>
            Current Content
          </Typography>
          <Paper
            variant="outlined"
            sx={{ flex: 1, overflowY: 'auto', p: 2, bgcolor: '#fafafa' }}
          >
            <ContentPreview content={currentContent} />
          </Paper>
        </Box>
      </Box>

      <Divider sx={{ mt: 2, mb: 1.5 }} />

      {/* Footer actions */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Button onClick={onClose} size="small">Close</Button>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            color="success"
            size="small"
            startIcon={<CheckCircleIcon />}
            onClick={() => handleConfirm('unit')}
            disabled={!hasContent || confirming}
          >
            Publish to Unit
          </Button>
          <Button
            variant="contained"
            color="success"
            size="small"
            startIcon={confirming ? <CircularProgress size={14} color="inherit" /> : <CheckCircleIcon />}
            onClick={() => handleConfirm('public')}
            disabled={!hasContent || confirming}
          >
            Confirm &amp; Publish
          </Button>
        </Box>
      </Box>
    </Box>
  );
}
