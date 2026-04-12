import React, { useEffect, useState } from 'react';
import {
  Box, Typography, Chip, Button, CircularProgress, Alert,
  Autocomplete, TextField, Paper, Stack,
  ToggleButton, ToggleButtonGroup, Tooltip,
} from '@mui/material';
import PublicIcon from '@mui/icons-material/Public';
import SchoolIcon from '@mui/icons-material/School';
import GroupsIcon from '@mui/icons-material/Groups';
import PersonIcon from '@mui/icons-material/Person';
import LockIcon from '@mui/icons-material/Lock';
import { api } from '../services/api';

/**
 * Scope levels — AWS-style least-privilege audience control.
 *
 *  public      → everyone (all students, public website)
 *  faculty     → all students enrolled in selected unit offerings
 *  cohort      → students in selected intake cohorts (if any exist)
 *  individual  → specific named students only
 *  staff       → staff/convenors only (internal, not visible to students)
 */
const SCOPES = [
  { value: 'public',     label: 'Public',     icon: <PublicIcon />,  desc: 'All students — visible on the public website' },
  { value: 'faculty',    label: 'By Unit',    icon: <SchoolIcon />,  desc: 'All students enrolled in selected unit offerings' },
  { value: 'individual', label: 'Individual', icon: <PersonIcon />,  desc: 'Specific named students only' },
  { value: 'staff',      label: 'Staff only', icon: <LockIcon />,    desc: 'Internal — staff and convenors only' },
];

function scopeToPayload(scope, selections) {
  const base = {
    target_all_students: false,
    target_students: [],
    target_offerings: [],
    target_intakes: [],
    visibility: 'public',
  };
  switch (scope) {
    case 'public':
      return { ...base, target_all_students: true, visibility: 'public' };
    case 'faculty':
      return { ...base, target_offerings: selections.offerings.map(o => o.id), visibility: 'unit' };
    case 'cohort':
      return { ...base, target_intakes: selections.intakes.map(i => i.id), visibility: 'unit' };
    case 'individual':
      return { ...base, target_students: selections.students.map(s => s.id), visibility: 'unit' };
    case 'staff':
      return { ...base, visibility: 'staff' };
    default:
      return base;
  }
}

function payloadToScope(event) {
  if (!event) return 'public';
  if (event.visibility === 'staff') return 'staff';
  if (event.target_all_students) return 'public';
  if ((event.target_students || []).length > 0) return 'individual';
  if ((event.target_intakes || []).length > 0) return 'cohort';
  if ((event.target_offerings || []).length > 0) return 'faculty';
  return 'public';
}

export default function EventTargeting({ eventId, onSave }) {
  const [scope, setScope] = useState('public');
  const [selections, setSelections] = useState({ students: [], offerings: [], intakes: [] });
  const [options, setOptions] = useState({ students: [], offerings: [], intakes: [] });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [previewCount, setPreviewCount] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  useEffect(() => { load(); }, [eventId]); // eslint-disable-line

  const load = async () => {
    try {
      setLoading(true);
      setError('');

      // Fetch in parallel — use actual API paths confirmed from DB
      const [eventRes, studentsRes, offeringsRes] = await Promise.all([
        api.get(`/core/events/${eventId}/`),
        api.get('/users/users/?user_type=student&page_size=500'),
        api.get('/academic/offerings/'),
      ]);

      const ev = eventRes.data;

      // Students: { id, email, first_name, last_name }
      const allStudents = studentsRes.data.results || studentsRes.data || [];

      // Offerings: { id, unit: { id, code, name }, semester, year }
      const allOfferings = offeringsRes.data.results || offeringsRes.data || [];

      // Intakes: no endpoint exists — skip silently
      let allIntakes = [];

      setOptions({ students: allStudents, offerings: allOfferings, intakes: allIntakes });

      // Restore current selections from event data
      const currentScope = payloadToScope(ev);
      setScope(currentScope);

      // target_offerings comes back as array of IDs from the serializer
      const offeringIds = (ev.target_offerings || []).map(o => (typeof o === 'object' ? o.id : o));
      const studentIds = (ev.target_students || []).map(s => (typeof s === 'object' ? s.id : s));
      const intakeIds = (ev.target_intakes || []).map(i => (typeof i === 'object' ? i.id : i));

      setSelections({
        students: allStudents.filter(s => studentIds.includes(s.id)),
        offerings: allOfferings.filter(o => offeringIds.includes(o.id)),
        intakes: allIntakes.filter(i => intakeIds.includes(i.id)),
      });
    } catch (err) {
      console.error('EventTargeting load error:', err);
      setError('Failed to load targeting options. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError('');
      const payload = scopeToPayload(scope, selections);
      const res = await api.patch(`/core/events/${eventId}/`, payload);
      setPreviewCount(null);
      if (onSave) onSave(res.data);
    } catch (err) {
      console.error('EventTargeting save error:', err);
      setError(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Failed to save audience settings');
    } finally {
      setSaving(false);
    }
  };

  const handlePreview = async () => {
    try {
      setPreviewLoading(true);
      const res = await api.get(`/core/events/${eventId}/targeted_students/`);
      const list = res.data.results || res.data || [];
      setPreviewCount(list.length);
    } catch (err) {
      setPreviewCount('error');
    } finally {
      setPreviewLoading(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, p: 2 }}>
        <CircularProgress size={18} />
        <Typography variant="body2" color="text.secondary">Loading audience options…</Typography>
      </Box>
    );
  }

  const currentScopeDef = SCOPES.find(s => s.value === scope);
  const needsOfferings = scope === 'faculty';
  const needsIntakes = scope === 'cohort';
  const needsStudents = scope === 'individual';

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>{error}</Alert>
      )}

      {/* Scope selector */}
      <Typography variant="caption" color="text.secondary" fontWeight={600}
        sx={{ textTransform: 'uppercase', mb: 1, display: 'block' }}>
        Audience Scope
      </Typography>

      <ToggleButtonGroup
        value={scope}
        exclusive
        onChange={(_, v) => { if (v) { setScope(v); setPreviewCount(null); } }}
        size="small"
        sx={{ flexWrap: 'wrap', gap: 0.5, mb: 1.5 }}
      >
        {SCOPES.map(s => (
          <Tooltip key={s.value} title={s.desc} placement="top">
            <ToggleButton value={s.value} sx={{ gap: 0.5, px: 1.5, py: 0.75 }}>
              {s.icon}
              <Typography variant="caption" sx={{ ml: 0.5 }}>{s.label}</Typography>
            </ToggleButton>
          </Tooltip>
        ))}
      </ToggleButtonGroup>

      <Paper variant="outlined" sx={{ p: 1.5, mb: 2, bgcolor: 'grey.50' }}>
        <Typography variant="body2" color="text.secondary">
          {currentScopeDef?.desc}
        </Typography>
      </Paper>

      {/* Unit/Offering selector */}
      {needsOfferings && (
        <Autocomplete
          multiple
          options={options.offerings}
          value={selections.offerings}
          onChange={(_, v) => setSelections(s => ({ ...s, offerings: v }))}
          getOptionLabel={o => `${o.unit?.code || ''} — ${o.unit?.name || ''} (${o.semester} ${o.year})`}
          isOptionEqualToValue={(a, b) => a.id === b.id}
          renderTags={(val, getProps) =>
            val.map((o, i) => (
              <Chip
                key={o.id}
                label={`${o.unit?.code || o.id} ${o.semester} ${o.year}`}
                size="small"
                {...getProps({ index: i })}
              />
            ))
          }
          renderInput={params => (
            <TextField {...params} label="Unit Offerings" size="small"
              helperText={`${options.offerings.length} offerings available`} />
          )}
          sx={{ mb: 2 }}
          noOptionsText="No offerings found"
        />
      )}

      {/* Intake/Cohort selector */}
      {needsIntakes && (
        options.intakes.length === 0 ? (
          <Alert severity="info" sx={{ mb: 2 }}>
            No intake cohorts found in the database. Use "By Unit" to target by class offering instead.
          </Alert>
        ) : (
          <Autocomplete
            multiple
            options={options.intakes}
            value={selections.intakes}
            onChange={(_, v) => setSelections(s => ({ ...s, intakes: v }))}
            getOptionLabel={i => `${i.semester} ${i.year}`}
            isOptionEqualToValue={(a, b) => a.id === b.id}
            renderTags={(val, getProps) =>
              val.map((i, idx) => (
                <Chip key={i.id} label={`${i.semester} ${i.year}`} size="small" {...getProps({ index: idx })} />
              ))
            }
            renderInput={params => <TextField {...params} label="Intake Cohorts" size="small" />}
            sx={{ mb: 2 }}
          />
        )
      )}

      {/* Individual student selector */}
      {needsStudents && (
        <Autocomplete
          multiple
          options={options.students}
          value={selections.students}
          onChange={(_, v) => setSelections(s => ({ ...s, students: v }))}
          getOptionLabel={s => `${s.email}${s.first_name ? ` (${s.first_name} ${s.last_name})` : ''}`}
          isOptionEqualToValue={(a, b) => a.id === b.id}
          renderTags={(val, getProps) =>
            val.map((s, i) => (
              <Chip key={s.id} label={s.email} size="small" {...getProps({ index: i })} />
            ))
          }
          renderInput={params => (
            <TextField {...params} label="Students" size="small"
              helperText={`${options.students.length} students available — type to search`} />
          )}
          filterOptions={(opts, { inputValue }) => {
            const q = inputValue.toLowerCase();
            return opts.filter(o =>
              o.email.toLowerCase().includes(q) ||
              `${o.first_name} ${o.last_name}`.toLowerCase().includes(q)
            ).slice(0, 50);
          }}
          sx={{ mb: 2 }}
          noOptionsText="No students found"
        />
      )}

      {/* Preview + Save */}
      <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
        <Button
          size="small"
          variant="outlined"
          onClick={handlePreview}
          disabled={previewLoading}
        >
          {previewLoading ? <CircularProgress size={14} sx={{ mr: 0.5 }} /> : null}
          Preview audience
        </Button>

        {previewCount !== null && previewCount !== 'error' && (
          <Chip
            size="small"
            color="info"
            label={`~${previewCount} student${previewCount !== 1 ? 's' : ''} targeted`}
          />
        )}
        {previewCount === 'error' && (
          <Typography variant="caption" color="error">Preview failed</Typography>
        )}

        <Box sx={{ flex: 1 }} />

        <Button
          size="small"
          variant="contained"
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? <CircularProgress size={14} color="inherit" sx={{ mr: 0.5 }} /> : null}
          Save Audience
        </Button>
      </Stack>
    </Box>
  );
}
